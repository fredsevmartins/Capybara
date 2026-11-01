"""Filesystem workspaces; originals are copied and never executed."""

import hashlib
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from .models import ROLE_DIR, FileEntry, Manifest, OpenReproError, Role, safe_path

METADATA = {"manifest.json", "ro-crate-metadata.json"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load_json(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise OpenReproError("Duplicate JSON object key")
            result[key] = value
        return result

    if path.stat().st_size > 4 * 1024 * 1024:
        raise OpenReproError("Metadata exceeds 4 MiB limit")

    def invalid_constant(value):
        raise OpenReproError("Nonfinite JSON numbers are forbidden")

    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=unique, parse_constant=invalid_constant
    )
    if not isinstance(value, dict):
        raise OpenReproError("Metadata must be a JSON object")
    return value


def bounded(root: Path, relative: str) -> Path:
    safe_path(relative)
    root = root.resolve()
    path = root / relative
    for ancestor in [path, *path.parents]:
        if ancestor == root:
            break
        if ancestor.is_symlink():
            raise OpenReproError("Symlinks are forbidden")
    if not path.resolve().is_relative_to(root):
        raise OpenReproError("Path escapes workspace")
    return path


def crate(manifest: Manifest) -> dict:
    return {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "identifier": str(manifest.identifier),
                "name": manifest.title,
                "description": manifest.description,
                "datePublished": manifest.created.isoformat(),
                "license": manifest.license,
                "author": [{"@id": f"#author-{i}"} for i in range(len(manifest.authors))],
                "hasPart": [{"@id": quote(f.path, safe="/")} for f in manifest.files],
            },
            *[
                {"@id": f"#author-{i}", "@type": "Person", "name": name}
                for i, name in enumerate(manifest.authors)
            ],
            *[
                {
                    "@id": quote(f.path, safe="/"),
                    "@type": "File",
                    "name": Path(f.path).name,
                    "description": f.description,
                    "contentSize": str(f.size),
                    "sha256": f.sha256,
                    "isBasedOn": [{"@id": quote(p, safe="/")} for p in f.derived_from],
                }
                for f in manifest.files
            ],
        ],
    }


def atomic_write(path: Path, data: bytes) -> None:
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".openrepro-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def save(root: Path, manifest: Manifest) -> None:
    # Each replacement is atomic; validation detects a cross-file interrupted update.
    atomic_write(bounded(root, "ro-crate-metadata.json"), json_bytes(crate(manifest)))
    atomic_write(bounded(root, "manifest.json"), json_bytes(manifest.model_dump(mode="json")))


def load(root: Path) -> Manifest:
    return Manifest.model_validate(load_json(bounded(root, "manifest.json")))


def create_experiment(
    root: Path, title: str, description: str, authors: list[str], **metadata
) -> Manifest:
    manifest = Manifest(title=title, description=description, authors=authors, **metadata)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    try:
        for directory in [*ROLE_DIR.values(), "provenance"]:
            (root / directory).mkdir(parents=True, exist_ok=True)
        save(root, manifest)
        for name, body, role in [
            (
                "README.md",
                f"# {title}\n\n{description}\n\nPackage integrity does not establish "
                "scientific validity.\n",
                Role.supplementary,
            ),
            (
                "provenance/provenance.json",
                json_bytes(
                    {"events": [{"action": "create", "at": manifest.created.isoformat()}]}
                ).decode(),
                Role.supplementary,
            ),
        ]:
            target = root / name
            target.write_text(body, encoding="utf-8")
            manifest.files.append(
                FileEntry(path=name, sha256=digest(target), size=target.stat().st_size, role=role)
            )
        save(root, manifest)
    except Exception:
        shutil.rmtree(root)
        raise
    return manifest


def _add_file(
    root: Path,
    source: Path,
    role: Role,
    description: str = "",
    derived_from: list[str] | None = None,
) -> FileEntry:
    root, source = Path(root), Path(source)
    from .validation import validate_experiment

    report = validate_experiment(root)
    if report["status"] == "FAIL":
        raise OpenReproError("Repair workspace validation failures before adding files")
    manifest = load(root)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):
        raise OpenReproError("Source symlinks are forbidden")
    if not source.is_file():
        raise OpenReproError("Source must be a regular file")
    relative = safe_path(f"{ROLE_DIR[role]}/{source.name}")
    if relative.casefold() in {f.path.casefold() for f in manifest.files}:
        raise OpenReproError("File already registered; choose a distinct name")
    relations = derived_from or []
    if any(p not in {f.path for f in manifest.files} for p in relations):
        raise OpenReproError("derived_from must reference registered files")
    target = bounded(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as output, source.open("rb") as input_file:
        shutil.copyfileobj(input_file, output)
    entry = FileEntry(
        path=relative,
        sha256=digest(target),
        size=target.stat().st_size,
        role=role,
        description=description,
        derived_from=relations,
    )
    manifest.files.append(entry)
    save(root, manifest)
    return entry


def inspect_experiment(root: Path) -> dict:
    from .validation import validate_experiment

    manifest = load(Path(root))
    return {
        "metadata": manifest.model_dump(mode="json"),
        "validation": validate_experiment(Path(root)),
    }


PROVENANCE = "provenance/provenance.json"
EDITABLE_METADATA = {
    "title",
    "description",
    "authors",
    "license",
    "domain",
    "keywords",
    "doi",
    "institution",
    "experimental_date",
    "reproduction",
}


@contextmanager
def transaction(root: Path, payloads: list[str]):
    """Restore affected bytes on handled failures; requires one trusted writer."""
    from .validation import validate_experiment

    root = Path(root)
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise OpenReproError("Workspace symlinks are forbidden")
    if validate_experiment(root)["status"] == "FAIL":
        raise OpenReproError("Repair workspace validation failures before editing")
    names = sorted(METADATA | {PROVENANCE} | set(payloads))
    backup = Path(tempfile.mkdtemp(prefix=".openrepro-backup-", dir=root.parent))
    retain_backup = False
    originals = set()
    try:
        for index, name in enumerate(names):
            path = bounded(root, name)
            if path.exists():
                shutil.copy2(path, backup / str(index))
                originals.add(name)
        (backup / "recovery.json").write_bytes(
            json_bytes(
                {"workspace": str(root.resolve()), "paths": names, "originals": sorted(originals)}
            )
        )
        try:
            yield
            if validate_experiment(root)["status"] == "FAIL":
                raise OpenReproError("Edit produced an invalid workspace")
        except BaseException:
            try:
                for index, name in enumerate(names):
                    path = bounded(root, name)
                    if name in originals:
                        os.replace(backup / str(index), path)
                    else:
                        path.unlink(missing_ok=True)
            except OSError as exc:
                retain_backup = True
                raise OpenReproError(
                    f"Rollback failed; recovery files retained at {backup}"
                ) from exc
            raise
    finally:
        if not retain_backup:
            shutil.rmtree(backup)


def record_event(root: Path, manifest: Manifest, action: str, **details) -> None:
    provenance = load_json(bounded(root, PROVENANCE))
    provenance["events"].append({"action": action, "at": datetime.now(UTC).isoformat(), **details})
    atomic_write(bounded(root, PROVENANCE), json_bytes(provenance))
    entry = next(f for f in manifest.files if f.path == PROVENANCE)
    entry.sha256 = digest(root / PROVENANCE)
    entry.size = (root / PROVENANCE).stat().st_size
    save(root, manifest)


def add_file(
    root: Path,
    source: Path,
    role: Role,
    description: str = "",
    derived_from: list[str] | None = None,
) -> FileEntry:
    root, source = Path(root), Path(source)
    role = Role(role)
    relative = safe_path(f"{ROLE_DIR[role]}/{source.name}")
    with transaction(root, [relative]):
        entry = _add_file(root, source, role, description, derived_from)
        record_event(root, load(root), "add", path=entry.path, sha256=entry.sha256)
    return entry


def update_metadata(root: Path, changes: dict) -> Manifest:
    """Validate explicit metadata changes while preserving identity and inventory."""
    root = Path(root)
    if not changes or set(changes) - EDITABLE_METADATA:
        raise OpenReproError("Supply editable metadata fields only")
    with transaction(root, []):
        data = load(root).model_dump(mode="json")
        data.update(changes)
        manifest = Manifest.model_validate(data)
        record_event(root, manifest, "update_metadata", fields=sorted(changes))
    return manifest


def remove_file(root: Path, relative: str) -> None:
    """Remove a registered payload unless other files depend on it."""
    root = Path(root)
    safe_path(relative)
    if relative in {"README.md", PROVENANCE}:
        raise OpenReproError("Required documents cannot be removed")
    with transaction(root, [relative]):
        manifest = load(root)
        entry = next((f for f in manifest.files if f.path == relative), None)
        if entry is None:
            raise OpenReproError("File is not registered")
        if any(relative in f.derived_from for f in manifest.files):
            raise OpenReproError("Remove dependent files first")
        bounded(root, relative).unlink()
        manifest.files.remove(entry)
        record_event(root, manifest, "remove", path=relative, sha256=entry.sha256)


def replace_file(root: Path, relative: str, source: Path) -> FileEntry:
    """Explicitly replace a payload; dependent results must be removed first."""
    root, source = Path(root), Path(source)
    safe_path(relative)
    if relative == PROVENANCE:
        raise OpenReproError("Provenance cannot be replaced")
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):
        raise OpenReproError("Source symlinks are forbidden")
    if not source.is_file():
        raise OpenReproError("Source must be a regular file")
    with transaction(root, [relative]):
        manifest = load(root)
        entry = next((f for f in manifest.files if f.path == relative), None)
        if entry is None:
            raise OpenReproError("File is not registered")
        if any(relative in f.derived_from for f in manifest.files):
            raise OpenReproError("Remove dependent files before replacing their input")
        old_hash = entry.sha256
        target = bounded(root, relative)
        if source.resolve() == target.resolve():
            raise OpenReproError("Replacement source must be a separate file")
        shutil.copyfile(source, target)
        entry.sha256, entry.size = digest(target), target.stat().st_size
        record_event(
            root, manifest, "replace", path=relative, previous_sha256=old_hash, sha256=entry.sha256
        )
    return entry
