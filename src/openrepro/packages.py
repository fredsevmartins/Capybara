"""Bounded ZIP import/export. Imported content is never executed."""

import os
import shutil
import stat
import tempfile
import zipfile
import zlib
from pathlib import Path

from .experiments import METADATA, bounded, load
from .models import OpenReproError, safe_path
from .validation import validate_experiment

MAX_FILES = 10000
MAX_TOTAL = 512 * 1024 * 1024
MAX_FILE = 128 * 1024 * 1024
MAX_RATIO = 200


def require_valid(root: Path) -> None:
    if validate_experiment(root)["status"] == "FAIL":
        raise OpenReproError("Experiment validation failed")


def check_entries(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    entries = archive.infolist()
    if not entries or len(entries) > MAX_FILES:
        raise OpenReproError("Empty archive or entry-count limit exceeded")
    seen = set()
    total = 0
    for entry in entries:
        safe_path(entry.filename)
        mode = entry.external_attr >> 16
        if entry.is_dir() or stat.S_IFMT(mode) not in (0, stat.S_IFREG) or entry.flag_bits & 1:
            raise OpenReproError("Only unencrypted regular-file entries are supported")
        if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise OpenReproError("Unsupported ZIP compression")
        key = entry.filename.casefold()
        if key in seen:
            raise OpenReproError("Duplicate or case-colliding archive entries")
        seen.add(key)
        total += entry.file_size
        if (
            entry.file_size > MAX_FILE
            or total > MAX_TOTAL
            or entry.file_size > max(entry.compress_size, 1) * MAX_RATIO
        ):
            raise OpenReproError("Archive resource limit exceeded")
    for name in seen:
        if any("/".join(name.split("/")[:i]) in seen for i in range(1, len(name.split("/")))):
            raise OpenReproError("Archive file/directory conflict")
    return entries


def import_experiment(package: Path, destination: Path) -> Path:
    package, destination = Path(package), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise OpenReproError("Import destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".openrepro-import-", dir=destination.parent))
    try:
        if package.stat().st_size > MAX_TOTAL:
            raise OpenReproError("Archive exceeds size limit")
        with zipfile.ZipFile(package) as archive:
            for entry in check_entries(archive):
                target = bounded(temporary, entry.filename)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, target.open("xb") as output:
                    copied = 0
                    while block := source.read(1024 * 1024):
                        copied += len(block)
                        if copied > min(entry.file_size, MAX_FILE):
                            raise OpenReproError("Expanded entry exceeds declared size")
                        output.write(block)
        require_valid(temporary)
        # Destination must not be concurrently created by another writer.
        if destination.exists():
            raise OpenReproError("Import destination already exists")
        temporary.rename(destination)
        return destination
    except (zipfile.BadZipFile, EOFError, RuntimeError, NotImplementedError, zlib.error) as exc:
        raise OpenReproError("Malformed or unsupported ZIP package") from exc
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def export_experiment(root: Path, output: Path) -> Path:
    root, output = Path(root), Path(output)
    if output.resolve().is_relative_to(root.resolve()):
        raise OpenReproError("Export destination must be outside experiment workspace")
    if output.exists() or output.is_symlink():
        raise OpenReproError("Export destination already exists")
    require_valid(root)
    manifest = load(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".openrepro-export-", dir=output.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
            for relative in sorted({f.path for f in manifest.files} | METADATA):
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                path = bounded(root, relative)
                if path.stat().st_size > MAX_FILE:
                    raise OpenReproError("File exceeds package size limit")
                with path.open("rb") as source, archive.open(info, "w") as target:
                    shutil.copyfileobj(source, target)
        with tempfile.TemporaryDirectory() as directory:
            import_experiment(temporary, Path(directory) / "verified")
        # Exclusive creation avoids silently replacing an existing export.
        with output.open("xb") as target, temporary.open("rb") as source:
            try:
                shutil.copyfileobj(source, target)
            except BaseException:
                output.unlink(missing_ok=True)
                raise
        return output
    finally:
        temporary.unlink(missing_ok=True)
