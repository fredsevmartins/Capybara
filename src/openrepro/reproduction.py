"""Explicit, offline Docker execution and independent result comparison."""

import hashlib
import json
import math
import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import Field, field_validator, model_validator

from . import __version__
from .experiments import bounded, digest, json_bytes, load
from .models import OpenReproError, StrictModel, safe_path
from .validation import validate_experiment

MAX_RESULT_BYTES = 16 * 1024 * 1024


class Comparison(StrictModel):
    reference: str
    output: str
    mode: Literal["exact", "json-numeric", "quantities"] = "exact"
    justification: str = ""
    units: dict[str, str] = Field(default_factory=dict)
    relative_tolerance: float = Field(default=1e-6, ge=0, allow_inf_nan=False)
    absolute_tolerance: float = Field(default=1e-9, ge=0, allow_inf_nan=False)

    _paths = field_validator("reference", "output")(safe_path)

    @field_validator("mode")
    @classmethod
    def supported_mode(cls, value):
        if value not in {"exact", "json-numeric", "quantities"}:
            raise ValueError("Comparison mode must be exact, json-numeric or quantities")
        return value

    @field_validator("units")
    @classmethod
    def unit_pointers(cls, values):
        import re

        if len(values) > 100:
            raise ValueError("Too many unit declarations")
        for pointer, unit in values.items():
            if not re.fullmatch(r"(?:/(?:[^~]|~[01])*)*", pointer) or len(pointer) > 512:
                raise ValueError("Use valid JSON pointers for quantity locations")
            if not unit.strip() or len(unit) > 100:
                raise ValueError("Unit names must be nonempty and bounded")
        return values

    @model_validator(mode="after")
    def quantity_policy(self):
        if self.mode == "quantities" and (not self.units or not self.justification):
            raise ValueError("Quantity comparisons require units and a tolerance justification")
        return self


class Recipe(StrictModel):
    schema_version: Literal["0.2"] = "0.2"
    image: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    command: list[str] = Field(min_length=1, max_length=128)
    comparisons: list[Comparison] = Field(min_length=1, max_length=100)
    dependency_files: list[str] = Field(default_factory=list, max_length=100)
    timeout_seconds: int = Field(default=60, ge=1, le=3600)
    memory_mb: int = Field(default=256, ge=32, le=4096)
    cpus: float = Field(default=1, ge=0.1, le=4, allow_inf_nan=False)
    output_mb: int = Field(default=64, ge=1, le=512)

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value):
        if value != "0.2":
            raise ValueError("Unsupported reproduction recipe version")
        return value

    @field_validator("command")
    @classmethod
    def valid_command(cls, values):
        if any(not arg or "\x00" in arg or len(arg) > 4096 for arg in values):
            raise ValueError("Command arguments must be nonempty and bounded")
        return values

    @field_validator("dependency_files")
    @classmethod
    def valid_dependencies(cls, values):
        return [safe_path(value) for value in values]

    @model_validator(mode="after")
    def unique_outputs(self):
        paths = [item.output.casefold() for item in self.comparisons]
        if len(paths) != len(set(paths)):
            raise ValueError("Comparison outputs must be distinct")
        return self


def _numeric_equal(expected, actual, relative, absolute):
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(expected) is type(actual) and expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if relative == 0 and absolute == 0:
            return expected == actual and all(
                not isinstance(value, float) or math.isfinite(value) for value in (expected, actual)
            )
        try:
            return (
                math.isfinite(expected)
                and math.isfinite(actual)
                and math.isclose(expected, actual, rel_tol=relative, abs_tol=absolute)
            )
        except OverflowError:
            return False
    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(
            _numeric_equal(value, actual[key], relative, absolute)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            _numeric_equal(left, right, relative, absolute) for left, right in zip(expected, actual)
        )
    return expected == actual


def _json_value(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise OpenReproError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise OpenReproError("Nonfinite JSON numbers are forbidden")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise OpenReproError("Nonfinite JSON numbers are forbidden")
        return number

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique,
        parse_constant=invalid_constant,
        parse_float=finite_float,
    )


def _pointer(value, pointer):
    try:
        for part in pointer.split("/")[1:] if pointer else []:
            key = part.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                if not key.isdecimal() or (len(key) > 1 and key.startswith("0")):
                    return None
                value = value[int(key)]
            else:
                value = value[key]
        return value
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def _differences(expected, actual, relative, absolute):
    result = []

    def visit(left, right, pointer):
        if len(result) >= 100:
            return
        if isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys():
            for key in left:
                visit(
                    left[key], right[key], pointer + "/" + key.replace("~", "~0").replace("/", "~1")
                )
        elif isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
            for index, (a, b) in enumerate(zip(left, right)):
                visit(a, b, pointer + "/" + str(index))
        elif not _numeric_equal(left, right, relative, absolute):

            def preview(value):
                if isinstance(value, (dict, list)):
                    return {
                        "type": type(value).__name__,
                        "preview": json.dumps(value, ensure_ascii=False)[:512],
                    }
                return value[:512] if isinstance(value, str) else value

            result.append({"pointer": pointer, "expected": preview(left), "actual": preview(right)})

    visit(expected, actual, "")
    return result


def compare_results(root: Path, outputs: Path, comparisons: list[Comparison]) -> dict:
    """Compare declared outputs only; never load or execute analysis code."""
    if not comparisons:
        raise OpenReproError("At least one comparison is required")
    if validate_experiment(root)["status"] == "FAIL":
        raise OpenReproError("Experiment validation failed")
    registered = {entry.path for entry in load(root).files}
    reports = []
    for item in comparisons:
        if item.reference not in registered:
            raise OpenReproError("Comparison reference must be registered")
        report = {
            "reference": item.reference,
            "output": item.output,
            "mode": item.mode,
            "relative_tolerance": item.relative_tolerance,
            "absolute_tolerance": item.absolute_tolerance,
        }
        try:
            reference, output = bounded(root, item.reference), bounded(outputs, item.output)
            for path in (reference, output):
                if not stat.S_ISREG(path.stat().st_mode):
                    raise OpenReproError("Result must be a regular file")
                if path.stat().st_size > MAX_RESULT_BYTES:
                    raise OpenReproError("Result exceeds 16 MiB comparison limit")
            if item.mode == "exact":
                equal = digest(reference) == digest(output)
            else:
                expected, actual = _json_value(reference), _json_value(output)
                unit_ok = True
                for pointer, unit in item.units.items():
                    for value in (expected, actual):
                        quantity = _pointer(value, pointer)
                        if (
                            not isinstance(quantity, dict)
                            or quantity.get("unit") != unit
                            or isinstance(quantity.get("value"), bool)
                            or not isinstance(quantity.get("value"), (int, float))
                        ):
                            unit_ok = False
                equal = unit_ok and _numeric_equal(
                    expected, actual, item.relative_tolerance, item.absolute_tolerance
                )
                report["differences"] = _differences(
                    expected, actual, item.relative_tolerance, item.absolute_tolerance
                )
                if not unit_ok:
                    report["unit_error"] = "Quantity units or value types differ from the recipe"
                report["justification"] = item.justification
                report["units"] = item.units
                if not item.justification:
                    report["warnings"] = ["Numeric tolerances have no recorded justification"]
            report.update(
                status="PASS" if equal else "FAIL",
                reference_sha256=digest(reference),
                output_sha256=digest(output),
            )
        except (ValueError, OSError, RecursionError):
            report.update(status="FAIL", error="Missing, unsafe, oversized or invalid result")
        reports.append(report)
    return {
        "status": "PASS" if all(r["status"] == "PASS" for r in reports) else "FAIL",
        "comparisons": reports,
        "scientific_validity": "NOT_EVALUATED",
    }


def _docker_env():
    environment = os.environ.copy()
    for name in (
        "DOCKER_HOST",
        "DOCKER_CONTEXT",
        "DOCKER_TLS",
        "DOCKER_TLS_VERIFY",
        "DOCKER_CERT_PATH",
    ):
        environment.pop(name, None)
    return environment


class DockerTimeout(OpenReproError):
    """The local Docker operation exceeded its deadline."""


def _docker(*args, timeout=30, check=True):
    try:
        return subprocess.run(
            ["docker", "--host=unix:///var/run/docker.sock", *args],
            env=_docker_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=check,
        )
    except subprocess.TimeoutExpired as exc:
        raise DockerTimeout("Docker operation timed out") from exc
    except (OSError, subprocess.CalledProcessError) as exc:
        raise OpenReproError(
            "Local Docker operation failed; check daemon and image availability"
        ) from exc


def reproduction_plan(root: Path, recipe: Recipe) -> dict:
    if validate_experiment(root)["status"] == "FAIL":
        raise OpenReproError("Experiment validation failed")
    manifest = load(root)
    registered = {entry.path: entry for entry in manifest.files}
    required = [c.reference for c in recipe.comparisons] + recipe.dependency_files
    if any(name not in registered for name in required):
        raise OpenReproError("References and dependency files must be registered")
    return {
        "recipe": recipe.model_dump(mode="json"),
        "experiment": str(manifest.identifier),
        "manifest_sha256": digest(root / "manifest.json"),
        "dependencies": [
            {"path": name, "sha256": registered[name].sha256} for name in recipe.dependency_files
        ],
        "execution_required": True,
        "scientific_validity": "NOT_EVALUATED",
    }


def _container_copy(container: str, source: str, destination: Path, limit: int) -> None:
    """Extract a bounded Docker tar stream without trusting archive paths or modes."""
    from .models import safe_path

    with tempfile.TemporaryFile() as archive:
        source_path = Path(source)
        if source.endswith("/."):
            parent, names = source[:-2], ["."]
        else:
            parent, names = str(source_path.parent), [source_path.name]
        maximum = limit + 4 * 1024 * 1024
        exceeded = []
        try:
            with subprocess.Popen(
                [
                    "docker",
                    "--host=unix:///var/run/docker.sock",
                    "exec",
                    container,
                    "tar",
                    "-C",
                    parent,
                    "-cf",
                    "-",
                    *names,
                ],
                env=_docker_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            ) as process:

                def drain():
                    total = 0
                    while block := process.stdout.read(64 * 1024):
                        total += len(block)
                        if total > maximum:
                            exceeded.append(True)
                            process.kill()
                            break
                        archive.write(block)

                reader = threading.Thread(target=drain, daemon=True)
                reader.start()
                try:
                    code = process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise OpenReproError("Container output collection timed out") from None
                finally:
                    reader.join(timeout=5)
                if reader.is_alive() or code or exceeded:
                    raise OpenReproError("Could not retrieve bounded container outputs")
        except OSError as exc:
            raise OpenReproError("Could not retrieve container outputs") from exc
        archive.seek(0)
        names, total = set(), 0
        try:
            with tarfile.open(fileobj=archive, mode="r|") as tar:
                for member in tar:
                    name = member.name
                    if name.startswith("./"):
                        name = name[2:]
                    name = name.rstrip("/")
                    if name in ("", ".") and member.isdir():
                        continue
                    safe_path(name)
                    key = name.casefold()
                    if (
                        key in names
                        or len(names) >= 1000
                        or not (member.isfile() or member.isdir())
                    ):
                        raise OpenReproError("Unsafe output type or output entry limit exceeded")
                    names.add(key)
                    target = bounded(destination, name)
                    if member.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue
                    total += member.size
                    if member.size > MAX_RESULT_BYTES or total > limit:
                        raise OpenReproError("Output size limit exceeded")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as input_file, target.open("xb") as output_file:
                        shutil.copyfileobj(input_file, output_file)
        except (tarfile.TarError, OSError) as exc:
            raise OpenReproError("Invalid container output archive") from exc


def recover_run(staging: Path) -> dict:
    """Cancel only a container matching both a locally saved run ID and Docker label."""
    import re

    from .experiments import atomic_write, load_json

    staging = Path(staging)
    journal = load_json(bounded(staging, "journal.json"))
    run_id = journal.get("run_id", "")
    if not re.fullmatch(r"[a-f0-9]{32}", run_id):
        raise OpenReproError("Invalid run journal")
    name = "openrepro-" + run_id
    matches = _docker(
        "ps",
        "--all",
        "--filter",
        f"name=^/{name}$",
        "--filter",
        f"label=org.openrepro.run={run_id}",
        "--format",
        "{{.Names}}",
    ).stdout.splitlines()
    if matches:
        if matches != [name]:
            raise OpenReproError("Run identity is ambiguous")
        _docker("rm", "--force", "--volumes", name)
    journal["state"] = "cancelled"
    atomic_write(bounded(staging, "journal.json"), json_bytes(journal))
    return {
        "status": "CANCELLED",
        "container_removed": bool(matches),
        "staging_preserved": str(staging),
    }


def reproduce(root: Path, recipe: Recipe, destination: Path, *, allow_execution=False) -> dict:
    """Run reviewed code with tmpfs output quotas and no writable host mounts."""
    from .experiments import atomic_write

    if not allow_execution:
        raise OpenReproError("Review the recipe and explicitly allow execution")
    if platform.system() != "Linux":
        raise OpenReproError("Reproduction currently requires Linux and local Docker")
    root, destination = Path(root).resolve(), Path(destination)
    if destination.resolve().is_relative_to(root):
        raise OpenReproError("Run destination must be outside the experiment")
    if destination.exists() or destination.is_symlink():
        raise OpenReproError("Run destination already exists")
    if "," in str(destination.resolve()):
        raise OpenReproError("Run destination must not contain commas")
    plan = reproduction_plan(root, recipe)
    runtime = json.loads(
        _docker(
            "info",
            "--format",
            '{"memory":{{json .MemoryLimit}},"swap":{{json .SwapLimit}},'
            '"pids":{{json .PidsLimit}},"cpu":{{json .CPUCfsQuota}},'
            '"security":{{json .SecurityOptions}},"version":{{json .ServerVersion}}}',
        ).stdout
    )
    if not all(runtime[key] for key in ("memory", "swap", "pids", "cpu")) or not any(
        value.startswith("name=seccomp") for value in runtime["security"]
    ):
        raise OpenReproError("Docker must support memory, swap, PID, CPU limits and seccomp")
    image = json.loads(
        _docker(
            "image",
            "inspect",
            "--format",
            '{"id":{{json .Id}},"os":{{json .Os}},'
            '"architecture":{{json .Architecture}},"repo_digests":{{json .RepoDigests}}}',
            recipe.image,
        ).stdout
    )
    if image["id"] != recipe.image or image["os"] != "linux":
        raise OpenReproError("Image identity or platform mismatch")
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_id = uuid4().hex
    container = "openrepro-" + run_id
    staging = Path(tempfile.mkdtemp(prefix=".openrepro-run-", dir=destination.parent)).resolve()
    journal = {
        "run_id": run_id,
        "state": "preparing",
        "destination": str(destination.resolve()),
        "experiment": str(root),
        "recipe_sha256": hashlib.sha256(json_bytes(recipe.model_dump(mode="json"))).hexdigest(),
    }
    journal_path = staging / "journal.json"
    atomic_write(journal_path, json_bytes(journal))
    created, retained = False, False
    try:
        inputs, outputs = staging / "experiment", staging / "outputs"
        shutil.copytree(root, inputs, symlinks=True)
        if (
            validate_experiment(inputs)["status"] == "FAIL"
            or digest(inputs / "manifest.json") != plan["manifest_sha256"]
        ):
            raise OpenReproError("Experiment changed while preparing reproduction")
        outputs.mkdir()
        run_uid, run_gid = os.getuid() or 65534, os.getgid() or 65534
        args = [
            "create",
            "--name",
            container,
            "--label",
            f"org.openrepro.run={run_id}",
            "--pull=never",
            "--network=none",
            "--read-only",
            "--no-healthcheck",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user",
            f"{run_uid}:{run_gid}",
            "--pids-limit=64",
            "--memory",
            f"{recipe.memory_mb}m",
            "--memory-swap",
            f"{recipe.memory_mb}m",
            "--cpus",
            str(recipe.cpus),
            "--ulimit",
            "fsize=16777216:16777216",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m,nr_inodes=2048,mode=1777",
            "--tmpfs",
            f"/output:rw,noexec,nosuid,size={recipe.output_mb}m,nr_inodes=2048,mode=700,uid={run_uid},gid={run_gid}",
            "--log-driver=local",
            "--log-opt=max-size=1m",
            "--log-opt=max-file=2",
            "--mount",
            f"type=bind,src={inputs},dst=/experiment,readonly",
            "--workdir=/experiment",
        ]
        for name in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "NO_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "no_proxy",
        ):
            args.extend(["--env", name + "="])
        args.extend(
            [
                "--env",
                "PYTHONDONTWRITEBYTECODE=1",
                "--entrypoint",
                "/bin/sh",
                recipe.image,
                "-c",
                "exec sleep infinity",
            ]
        )
        started = datetime.now(UTC).isoformat()
        created = True
        _docker(*args)
        journal["state"] = "running"
        atomic_write(journal_path, json_bytes(journal))
        _docker("start", container)
        timed_out = False
        try:
            result = _docker(
                "exec",
                container,
                "/bin/sh",
                "-c",
                'exec "$@" >/tmp/openrepro-stdout 2>/tmp/openrepro-stderr',
                "openrepro",
                *recipe.command,
                timeout=recipe.timeout_seconds,
                check=False,
            )
            exit_code = result.returncode
        except DockerTimeout:
            timed_out, exit_code = True, None
        _container_copy(container, "/output/.", outputs, recipe.output_mb * 1024 * 1024)
        log_directory = staging / "logs"
        log_directory.mkdir()
        for stream in ("stdout", "stderr"):
            _container_copy(container, "/tmp/openrepro-" + stream, log_directory, MAX_RESULT_BYTES)
            with (log_directory / ("openrepro-" + stream)).open("rb") as log:
                content = log.read(1024 * 1024).decode("utf-8", errors="replace")
            (staging / (stream + ".txt")).write_text(content, encoding="utf-8")
        _docker("rm", "--force", "--volumes", container)
        created = False
        comparison = compare_results(inputs, outputs, recipe.comparisons)
        report = {
            **plan,
            "image": image,
            "runtime": runtime,
            "run_id": run_id,
            "openrepro_version": __version__,
            "started": started,
            "finished": datetime.now(UTC).isoformat(),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "comparison": comparison,
            "recipe_sha256": journal["recipe_sha256"],
            "output_quota_mb": recipe.output_mb,
            "status": "PASS" if exit_code == 0 and comparison["status"] == "PASS" else "FAIL",
        }
        atomic_write(staging / "report.json", json_bytes(report))
        shutil.rmtree(inputs)
        shutil.rmtree(log_directory)
        journal["state"] = "finished"
        atomic_write(journal_path, json_bytes(journal))
        if destination.exists() or destination.is_symlink():
            raise OpenReproError("Run destination already exists")
        staging.rename(destination)
        return report
    finally:
        try:
            cleanup = (
                _docker("rm", "--force", "--volumes", container, check=False) if created else None
            )
            if cleanup is not None and cleanup.returncode:
                retained = True
        except OpenReproError:
            retained = True
        if staging.exists() and not retained:
            shutil.rmtree(staging)
        if retained:
            raise OpenReproError(f"Docker cleanup failed; recovery journal retained at {staging}")
