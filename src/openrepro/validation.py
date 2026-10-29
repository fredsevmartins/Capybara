"""Offline structural validation of the supported RO-Crate profile."""

from pathlib import Path

from .experiments import METADATA, bounded, crate, digest, load, load_json
from .models import OpenReproError


def validate_experiment(root: Path) -> dict:
    issues = []

    def issue(status, code, message):
        issues.append({"status": status, "code": code, "message": message})

    try:
        root = Path(root)
        manifest = load(root)
        paths = [f.path for f in manifest.files]
        if len({p.casefold() for p in paths}) != len(paths):
            issue("FAIL", "duplicate", "Duplicate or case-colliding manifest entries")
        if any(p in METADATA for p in paths):
            issue("FAIL", "reserved", "Manifest may not inventory metadata documents")
        if not {"README.md", "provenance/provenance.json"}.issubset(paths):
            issue("FAIL", "required", "README and provenance must be inventoried")
        for entry in manifest.files:
            path = bounded(root, entry.path)
            if not path.is_file():
                issue("FAIL", "missing", f"Missing file: {entry.path}")
            elif path.stat().st_size != entry.size or digest(path) != entry.sha256:
                issue("FAIL", "checksum", f"Content differs: {entry.path}")
            if any(p not in paths or p == entry.path for p in entry.derived_from):
                issue("FAIL", "relationship", f"Invalid derived_from: {entry.path}")
        actual = set()
        for path in root.rglob("*"):
            if path.is_symlink():
                raise OpenReproError("Symlinks are forbidden")
            if path.is_file():
                actual.add(path.relative_to(root).as_posix())
        if actual != set(paths) | METADATA:
            issue("FAIL", "inventory", "Inventory must match all workspace files")
        # Strict generated profile: check required fields and cross-document relationships.
        if load_json(bounded(root, "ro-crate-metadata.json")) != crate(manifest):
            issue("FAIL", "ro-crate", "RO-Crate metadata differs from manifest profile")
        provenance = load_json(bounded(root, "provenance/provenance.json"))
        if not isinstance(provenance.get("events"), list):
            issue("FAIL", "provenance", "Provenance events must be a list")
        if not manifest.reproduction:
            issue("WARN", "reproduction", "No reproduction instructions supplied")
    except (ValueError, OSError, KeyError, TypeError, RecursionError):
        issue("FAIL", "metadata", "Unreadable, unsafe, or invalid workspace metadata")
    status = (
        "FAIL" if any(i["status"] == "FAIL" for i in issues) else ("WARN" if issues else "PASS")
    )
    return {"status": status, "issues": issues, "scientific_validity": "NOT_EVALUATED"}
