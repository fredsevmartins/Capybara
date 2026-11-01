"""Resolve binary Python dependencies, record hashes and build offline environments."""

import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .experiments import (
    _add_file,
    bounded,
    digest,
    json_bytes,
    load,
    record_event,
    transaction,
)
from .models import OpenReproError, Role, StrictModel, safe_path
from .reproduction import _docker, _docker_env
from .validation import validate_experiment


class EnvironmentSpec(StrictModel):
    schema_version: Literal["1"] = "1"
    base_image: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    requirements: str | None = None
    wheels: list[str] = Field(default_factory=list, max_length=256)

    @field_validator("schema_version")
    @classmethod
    def supported(cls, value):
        if value != "1":
            raise ValueError("Unsupported environment schema")
        return value

    @field_validator("requirements")
    @classmethod
    def lock_path(cls, value):
        return safe_path(value) if value is not None else None

    @field_validator("wheels")
    @classmethod
    def wheel_paths(cls, values):
        for value in values:
            safe_path(value)
            if not value.endswith(".whl"):
                raise ValueError("Only binary wheels are supported")
        if len({Path(value).name.casefold() for value in values}) != len(values):
            raise ValueError("Wheel names must be unique")
        return values

    @model_validator(mode="after")
    def paired(self):
        if bool(self.requirements) != bool(self.wheels):
            raise ValueError("Provide both a hash lock and wheels, or neither")
        return self


def environment_plan(root: Path, spec: EnvironmentSpec) -> dict:
    if validate_experiment(root)["status"] == "FAIL":
        raise OpenReproError("Experiment validation failed")
    inventory = {item.path: item for item in load(root).files}
    names = ([spec.requirements] if spec.requirements else []) + spec.wheels
    if any(name not in inventory for name in names):
        raise OpenReproError("Environment files must be registered")
    inputs = {name: inventory[name].sha256 for name in sorted(names)}
    fingerprint = hashlib.sha256(
        json_bytes({"builder_revision": 1, "spec": spec.model_dump(), "inputs": inputs})
    ).hexdigest()
    return {
        "builder_revision": 1,
        "spec": spec.model_dump(),
        "inputs": inputs,
        "fingerprint": fingerprint,
    }


def build_environment(root: Path, spec: EnvironmentSpec, *, allow_build=False) -> dict:
    if not allow_build:
        raise OpenReproError("Review the environment and explicitly allow building")
    plan = environment_plan(root, spec)
    base = json.loads(
        _docker(
            "image", "inspect", "--format", '{"id":{{json .Id}},"os":{{json .Os}}}', spec.base_image
        ).stdout
    )
    if base != {"id": spec.base_image, "os": "linux"}:
        raise OpenReproError("A local immutable Linux base image is required")
    tag = "openrepro-env:" + plan["fingerprint"]
    cached = _docker(
        "image",
        "inspect",
        "--format",
        '{{index .Config.Labels "org.openrepro.environment"}}',
        tag,
        check=False,
    )
    if cached.returncode == 0 and cached.stdout.strip() == plan["fingerprint"]:
        image = _docker("image", "inspect", "--format", "{{.Id}}", tag).stdout.strip()
        return {**plan, "image": image, "cached": True}
    # A local tag avoids any implicit registry resolution of a bare image ID.
    base_tag = "openrepro-base:" + spec.base_image.split(":")[1]
    _docker("tag", spec.base_image, base_tag)
    with tempfile.TemporaryDirectory(prefix="openrepro-build-") as directory:
        context = Path(directory)
        wheels = context / "wheels"
        wheels.mkdir()
        for name in spec.wheels:
            copied = wheels / Path(name).name
            shutil.copyfile(bounded(root, name), copied)
            if digest(copied) != plan["inputs"][name]:
                raise OpenReproError("Wheel changed while preparing environment")
        dockerfile = f'FROM {base_tag}\nLABEL org.openrepro.environment="{plan["fingerprint"]}"\n'
        if spec.requirements:
            lock = context / "requirements.lock"
            shutil.copyfile(bounded(root, spec.requirements), lock)
            if digest(lock) != plan["inputs"][spec.requirements]:
                raise OpenReproError("Lock changed while preparing environment")
            text = lock.read_text(encoding="utf-8")
            # Do not allow a lock to add indexes, URLs, editable installs or nested requirements.
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if not re.fullmatch(
                    r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+!-]+(?: --hash=sha256:[a-f0-9]{64})+", line
                ):
                    raise OpenReproError("Use exact package versions with SHA-256 hashes only")
            dockerfile += (
                "COPY wheels /openrepro-wheels\n"
                "COPY requirements.lock /openrepro-requirements.lock\n"
                "RUN python -m pip --isolated install --no-cache-dir --no-compile "
                "--force-reinstall --no-index "
                "--require-hashes --only-binary=:all: --find-links=/openrepro-wheels "
                "-r /openrepro-requirements.lock && "
                "rm -rf /openrepro-wheels /openrepro-requirements.lock\n"
            )
        (context / "Dockerfile").write_text(dockerfile, encoding="utf-8")
        _docker(
            "build",
            "--network=none",
            "--pull=false",
            "--force-rm",
            "--tag",
            tag,
            str(context),
            timeout=600,
        )
    image = _docker("image", "inspect", "--format", "{{.Id}}", tag).stdout.strip()
    return {**plan, "image": image, "cached": False}


def lock_environment(
    root: Path, requirements: str, base_image: str, destination: Path, *, allow_download=False
) -> dict:
    """Resolve wheels for the matching host interpreter and register exact hashed inputs."""
    if not allow_download:
        raise OpenReproError("Dependency resolution requires explicit download permission")
    if platform.system() != "Linux":
        raise OpenReproError("Dependency resolution currently requires Linux")
    try:
        import pip  # noqa: F401
        from packaging.requirements import Requirement
    except ImportError as exc:
        raise OpenReproError("Install openrepro[environment] to resolve dependencies") from exc
    spec = EnvironmentSpec(base_image=base_image)
    root, destination = Path(root), Path(destination)
    if (
        destination.exists()
        or destination.is_symlink()
        or destination.resolve().is_relative_to(root.resolve())
    ):
        raise OpenReproError("Choose a new dependency destination outside the experiment")
    if validate_experiment(root)["status"] == "FAIL" or requirements not in {
        f.path for f in load(root).files
    }:
        raise OpenReproError("Requirements must be registered in a valid experiment")
    source = bounded(root, requirements)
    if source.stat().st_size > 1024 * 1024:
        raise OpenReproError("Requirements exceed 1 MiB")
    lines = []
    for line in source.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        requirement = Requirement(line)
        if requirement.url:
            raise OpenReproError("Direct URLs are not supported; use registry packages")
        lines.append(str(requirement))
    if not lines or len(lines) > 100:
        raise OpenReproError("Provide between 1 and 100 registry requirements")
    interpreter = json.loads(
        _docker(
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user=65534:65534",
            "--entrypoint=python",
            spec.base_image,
            "-c",
            "import json,sys,platform; "
            "print(json.dumps([list(sys.version_info[:2]),platform.machine(),platform.libc_ver()]))",
        ).stdout
    )
    if interpreter[:2] != [list(sys.version_info[:2]), platform.machine()]:
        raise OpenReproError(
            "Resolver and base image must have the same Python minor version and architecture"
        )
    if interpreter[2][0] != "glibc":
        raise OpenReproError("Automatic resolution requires a glibc-based Python image")
    try:
        major, minor = map(int, interpreter[2][1].split(".")[:2])
    except (ValueError, IndexError) as exc:
        raise OpenReproError("Could not identify base-image glibc") from exc
    if major != 2 or not 5 <= minor <= 100:
        raise OpenReproError("Unsupported base-image glibc version")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".openrepro-lock-", dir=destination.parent
    ) as directory:
        staging = Path(directory)
        sanitized = staging / "requirements.in"
        sanitized.write_text("\n".join(lines) + "\n", encoding="utf-8")
        wheels = staging / "wheels"
        command = [
            sys.executable,
            "-m",
            "pip",
            "--isolated",
            "download",
            "--only-binary=:all:",
            "--dest",
            str(wheels),
            "-r",
            str(sanitized),
        ]
        abi = f"cp{sys.version_info.major}{sys.version_info.minor}"
        command.extend(
            [
                "--python-version",
                f"{sys.version_info.major}.{sys.version_info.minor}",
                "--implementation",
                "cp",
                "--abi",
                abi,
                "--abi",
                "abi3",
                "--abi",
                "none",
            ]
        )
        for version in range(minor, 4, -1):
            command.extend(["--platform", f"manylinux_2_{version}_{platform.machine()}"])
        for alias in ("manylinux2014", "manylinux2010", "manylinux1"):
            command.extend(["--platform", alias + "_" + platform.machine()])
        # Use the configured system CA bundle, retaining HTTPS/proxy verification.
        ca = Path("/etc/ssl/certs/ca-certificates.crt")
        if ca.is_file():
            command.extend(["--cert", str(ca)])
        try:
            subprocess.run(command, capture_output=True, timeout=300, check=True, env=_docker_env())
        except (OSError, subprocess.SubprocessError) as exc:
            raise OpenReproError(
                "Wheel resolution failed; check package names, registry access and CA trust"
            ) from exc
        wheel_files = sorted(wheels.glob("*.whl"))
        if (
            not wheel_files
            or len(wheel_files) > 256
            or sum(p.stat().st_size for p in wheel_files) > 256 * 1024 * 1024
            or any(p.stat().st_size > 128 * 1024 * 1024 for p in wheel_files)
        ):
            raise OpenReproError("Resolved wheelhouse exceeds limits")
        locked = []
        for wheel in wheel_files:
            with zipfile.ZipFile(wheel) as archive:
                metadata = [
                    name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
                ]
                if len(metadata) != 1 or archive.getinfo(metadata[0]).file_size > 1024 * 1024:
                    raise OpenReproError("Invalid wheel metadata")
                values = BytesParser().parsebytes(archive.read(metadata[0]))
            name, version = values["Name"], values["Version"]
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", name or "") or not re.fullmatch(
                r"[A-Za-z0-9_.+!-]+", version or ""
            ):
                raise OpenReproError("Invalid wheel distribution identity")
            locked.append(f"{name}=={version} --hash=sha256:{digest(wheel)}")
        lock = staging / "requirements.lock"
        lock.write_text("\n".join(sorted(locked)) + "\n", encoding="utf-8")
        files = [lock, *wheel_files]
        paths = ["supplementary/" + f.name for f in files]
        with transaction(root, paths):
            for file in files:
                _add_file(
                    root, file, Role.supplementary, "Locked environment input", [requirements]
                )
            record_event(
                root, load(root), "lock_environment", requirements=requirements, files=paths
            )
            spec = EnvironmentSpec(base_image=base_image, requirements=paths[0], wheels=paths[1:])
            (staging / "environment.json").write_bytes(json_bytes(spec.model_dump()))
            sanitized.unlink()
            staging.rename(destination)
    return {
        "environment": str(destination / "environment.json"),
        "registered": paths,
        "base_image": base_image,
    }
