"""Explicit, offline Docker execution and independent result comparison."""

import hashlib
import json
import math
import os
import platform
import shutil
import stat
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
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
    mode: str = "exact"
    relative_tolerance: float = Field(default=1e-6, ge=0, allow_inf_nan=False)
    absolute_tolerance: float = Field(default=1e-9, ge=0, allow_inf_nan=False)

    _paths = field_validator("reference", "output")(safe_path)

    @field_validator("mode")
    @classmethod
    def supported_mode(cls, value):
        if value not in {"exact", "json-numeric"}:
            raise ValueError("Comparison mode must be exact or json-numeric")
        return value


class Recipe(StrictModel):
    schema_version: str = "0.2"
    image: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    command: list[str] = Field(min_length=1, max_length=128)
    comparisons: list[Comparison] = Field(min_length=1, max_length=100)
    dependency_files: list[str] = Field(default_factory=list, max_length=100)
    timeout_seconds: int = Field(default=60, ge=1, le=3600)
    memory_mb: int = Field(default=256, ge=32, le=4096)
    cpus: float = Field(default=1, ge=0.1, le=4, allow_inf_nan=False)

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

    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=unique, parse_constant=invalid_constant
    )


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
                equal = _numeric_equal(
                    _json_value(reference),
                    _json_value(output),
                    item.relative_tolerance,
                    item.absolute_tolerance,
                )
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


def reproduce(root: Path, recipe: Recipe, destination: Path, *, allow_execution=False) -> dict:
    """Run a user-reviewed recipe; no host execution fallback or automatic image pull."""
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
    container = "openrepro-" + uuid4().hex
    with tempfile.TemporaryDirectory(prefix=".openrepro-run-", dir=destination.parent) as directory:
        staging = Path(directory).resolve()
        inputs, outputs = staging / "experiment", staging / "outputs"
        shutil.copytree(root, inputs, symlinks=True)
        if (
            validate_experiment(inputs)["status"] == "FAIL"
            or digest(inputs / "manifest.json") != plan["manifest_sha256"]
        ):
            raise OpenReproError("Experiment changed while preparing reproduction")
        outputs.mkdir(mode=0o700)
        run_uid, run_gid = os.getuid() or 65534, os.getgid() or 65534
        if os.getuid() == 0:
            os.chown(outputs, run_uid, run_gid)
        args = [
            "create",
            "--name",
            container,
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
            "/tmp:rw,noexec,nosuid,size=64m,mode=1777",
            "--log-driver=local",
            "--log-opt=max-size=1m",
            "--log-opt=max-file=2",
            "--mount",
            f"type=bind,src={inputs},dst=/experiment,readonly",
            "--mount",
            f"type=bind,src={outputs},dst=/output",
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
                recipe.command[0],
                recipe.image,
                *recipe.command[1:],
            ]
        )
        started = datetime.now(UTC).isoformat()
        created = False
        try:
            _docker(*args)
            created = True
            _docker("start", container)
            timed_out = False
            try:
                result = _docker("wait", container, timeout=recipe.timeout_seconds)
                exit_code = int(result.stdout.strip())
            except DockerTimeout:
                timed_out = True
                _docker("kill", container, check=False)
                exit_code = None
            logs = _docker("logs", "--tail", "200", container, check=False)
            (staging / "stdout.txt").write_text(logs.stdout[: 1024 * 1024], encoding="utf-8")
            (staging / "stderr.txt").write_text(logs.stderr[: 1024 * 1024], encoding="utf-8")
        finally:
            cleanup = _docker("rm", "--force", "--volumes", container, check=False)
            if created and cleanup.returncode:
                raise OpenReproError(f"Docker cleanup failed; remove container {container}")
        count, size = 0, 0
        for path in outputs.rglob("*"):
            count += 1
            mode = path.lstat().st_mode
            if count > 1000 or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise OpenReproError("Unsafe output type or output entry limit exceeded")
            if stat.S_ISREG(mode):
                size += path.stat().st_size
            if size > 64 * 1024 * 1024:
                raise OpenReproError("Outputs exceed 64 MiB retention limit")
        comparison = compare_results(inputs, outputs, recipe.comparisons)
        report = {
            **plan,
            "image": image,
            "runtime": runtime,
            "openrepro_version": __version__,
            "started": started,
            "finished": datetime.now(UTC).isoformat(),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "comparison": comparison,
            "recipe_sha256": hashlib.sha256(json_bytes(recipe.model_dump(mode="json"))).hexdigest(),
            "status": "PASS" if exit_code == 0 and comparison["status"] == "PASS" else "FAIL",
        }
        (staging / "report.json").write_bytes(json_bytes(report))
        shutil.rmtree(inputs)
        # Caller must own the parent and use a single writer, as for package import.
        if destination.exists() or destination.is_symlink():
            raise OpenReproError("Run destination already exists")
        staging.rename(destination)
    return report
