"""Explicit local RO-Crate 1.1 conversion without remote contexts or code execution."""

import shutil
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .experiments import bounded, create_experiment, digest, load_json, record_event
from .models import FileEntry, OpenReproError, Role, safe_path
from .validation import validate_experiment


def _local_id(value):
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise OpenReproError("Only local file identifiers can be converted")
    path = unquote(parsed.path, errors="strict")
    return safe_path(path.removeprefix("./"))


def _types(value):
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
        raise OpenReproError("RO-Crate entity types must be strings or lists of strings")
    return values


def convert_crate(source: Path, destination: Path, *, license=None, authors=None) -> dict:
    source, destination = Path(source), Path(destination)
    if (
        destination.exists()
        or destination.is_symlink()
        or destination.resolve().is_relative_to(source.resolve())
    ):
        raise OpenReproError("Choose a new conversion destination outside the source crate")
    metadata = bounded(source, "ro-crate-metadata.json")
    original = load_json(metadata)
    context = original.get("@context")
    if context != "https://w3id.org/ro/crate/1.1/context" and not (
        isinstance(context, list) and "https://w3id.org/ro/crate/1.1/context" in context
    ):
        raise OpenReproError("Conversion supports the local RO-Crate 1.1 context only")
    graph = original.get("@graph")
    if not isinstance(graph, list) or len(graph) > 10000:
        raise OpenReproError("Invalid or oversized RO-Crate graph")
    nodes = {}
    for node in graph:
        if (
            not isinstance(node, dict)
            or not isinstance(node.get("@id"), str)
            or node["@id"] in nodes
        ):
            raise OpenReproError("Graph identifiers must be unique")
        nodes[node["@id"]] = node
    root = nodes.get("./", {})
    if "Dataset" not in _types(root.get("@type", [])):
        raise OpenReproError("A root Dataset with identifier ./ is required")
    declared_license = license or root.get("license")
    if isinstance(declared_license, dict):
        declared_license = declared_license.get("@id")
    if not isinstance(declared_license, str) or not declared_license.strip():
        raise OpenReproError("Supply --license; the crate does not declare a usable license")
    if not authors:
        authors = []
        value = root.get("author", [])
        for author in value if isinstance(value, list) else [value]:
            if isinstance(author, str):
                authors.append(author)
            elif isinstance(author, dict):
                name = author.get("name") or nodes.get(author.get("@id"), {}).get("name")
                if name:
                    authors.append(name)
    if not authors:
        raise OpenReproError("Supply --author; no author names could be resolved")
    files, visiting = [], set()

    def visit(node):
        identifier = node.get("@id")
        if identifier in visiting:
            raise OpenReproError("Cyclic hasPart relationships")
        visiting.add(identifier)
        parts = node.get("hasPart", [])
        if not isinstance(parts, list):
            parts = [parts]
        for part in parts:
            child_id = part.get("@id") if isinstance(part, dict) else part
            if not isinstance(child_id, str):
                raise OpenReproError("hasPart identifiers must be strings")
            child = nodes.get(child_id)
            if child is None:
                raise OpenReproError("Every hasPart identifier must resolve within the graph")
            kind = _types(child.get("@type", []))
            if "File" in kind:
                files.append((_local_id(child_id), child))
            elif "Dataset" in kind:
                visit(child)
            else:
                raise OpenReproError("hasPart must reference a File or Dataset")
        visiting.remove(identifier)

    try:
        visit(root)
    except RecursionError as exc:
        raise OpenReproError("RO-Crate nesting exceeds the supported depth") from exc
    if not files or len(files) > 9990 or len({name.casefold() for name, _ in files}) != len(files):
        raise OpenReproError("Crate must contain distinct portable local files")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".openrepro-crate-", dir=destination.parent
    ) as directory:
        staging = Path(directory) / "converted"
        manifest = create_experiment(
            staging,
            root.get("name") or "Imported RO-Crate",
            root.get("description") or "Explicit conversion of a local RO-Crate",
            authors,
            license=declared_license,
            reproduction="Review original crate metadata and analysis before reproduction",
        )
        mapping = {}
        total = 0
        for relative, node in files:
            original_file = bounded(source, relative)
            if not original_file.is_file() or original_file.stat().st_size > 128 * 1024 * 1024:
                raise OpenReproError("Crate payload is missing or exceeds the file limit")
            total += original_file.stat().st_size
            if total > 512 * 1024 * 1024:
                raise OpenReproError("Crate exceeds 512 MiB total payload limit")
            if node.get("sha256") and node["sha256"] != digest(original_file):
                raise OpenReproError("Source crate checksum mismatch")
            if "contentSize" in node and str(node["contentSize"]) != str(
                original_file.stat().st_size
            ):
                raise OpenReproError("Source crate size mismatch")
            target_name = relative
            if relative in {
                "manifest.json",
                "ro-crate-metadata.json",
                "README.md",
                "provenance/provenance.json",
                "supplementary/source-ro-crate.json",
            }:
                target_name = "supplementary/imported/" + relative
            target = bounded(staging, target_name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with original_file.open("rb") as input_file, target.open("xb") as output:
                shutil.copyfileobj(input_file, output)
            role = (
                Role.raw
                if relative.startswith("data/")
                else (Role.script if relative.startswith("analysis/") else Role.supplementary)
            )
            manifest.files.append(
                FileEntry(
                    path=target_name,
                    sha256=digest(target),
                    size=target.stat().st_size,
                    role=role,
                    description=str(node.get("description", "")),
                )
            )
            mapping[relative] = target_name
        archived = staging / "supplementary/source-ro-crate.json"
        shutil.copyfile(metadata, archived)
        manifest.files.append(
            FileEntry(
                path="supplementary/source-ro-crate.json",
                sha256=digest(archived),
                size=archived.stat().st_size,
                role=Role.supplementary,
                description="Unmodified original RO-Crate graph",
            )
        )
        record_event(staging, manifest, "convert_crate", source_metadata_sha256=digest(metadata))
        if validate_experiment(staging)["status"] == "FAIL":
            raise OpenReproError("Converted crate failed package validation")
        staging.rename(destination)
    return {
        "workspace": str(destination),
        "mapping": mapping,
        "source_metadata_sha256": digest(metadata),
        "scientific_validity": "NOT_EVALUATED",
    }
