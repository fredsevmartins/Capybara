"""Validate distribution metadata and file inventories without publishing anything."""

import argparse
import hashlib
import json
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

from packaging.utils import canonicalize_name

from openrepro import __version__


def check(directory: Path):
    wheel = directory / f"openrepro-{__version__}-py3-none-any.whl"
    source = directory / f"openrepro-{__version__}.tar.gz"
    with zipfile.ZipFile(wheel) as archive:
        metadata_names = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        assert len(metadata_names) == 1, "Missing or duplicate wheel metadata"
        metadata = BytesParser().parsebytes(archive.read(metadata_names[0]))
        assert canonicalize_name(metadata["Name"]) == "openrepro"
        assert metadata["Version"] == __version__
        source_root = Path(__file__).resolve().parents[1] / "src/openrepro"
        for module_file in source_root.glob("*.py"):
            assert archive.read("openrepro/" + module_file.name) == module_file.read_bytes(), (
                "Stale wheel module",
                module_file.name,
            )
        for module in (
            "api",
            "catalog",
            "environment",
            "experience",
            "interoperability",
            "reproduction",
            "zenodo",
        ):
            assert f"openrepro/{module}.py" in archive.namelist(), module
    with tarfile.open(source, "r:gz") as archive:
        names = archive.getnames()
        prefix = f"openrepro-{__version__}/"
        for required in (
            "uv.lock",
            "README.md",
            "docs/launch-checklist.md",
            "examples/iris/iris.csv",
            "examples/iris/source.json",
            "tests/test_release_contract.py",
        ):
            assert prefix + required in names, required
    return {
        "version": __version__,
        "artifacts": [
            {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in (wheel, source)
        ],
        "status": "PASS",
        "published": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    print(json.dumps(check(parser.parse_args().dist), indent=2))
