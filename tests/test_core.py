import hashlib
import json

import pytest
from pydantic import ValidationError

from openrepro.experiments import (
    add_file,
    create_experiment,
    digest,
    inspect_experiment,
    load,
    save,
)
from openrepro.models import Manifest, OpenReproError, Role
from openrepro.packages import export_experiment, import_experiment
from openrepro.validation import validate_experiment


@pytest.fixture
def experiment(tmp_path):
    root = tmp_path / "experiment"
    create_experiment(
        root, "Study", "Synthetic study", ["Researcher"], reproduction="Read protocol"
    )
    return root


def test_create_metadata_and_inspect(experiment):
    report = inspect_experiment(experiment)
    assert report["metadata"]["title"] == "Study"
    assert report["validation"]["status"] == "PASS"
    assert report["validation"]["scientific_validity"] == "NOT_EVALUATED"
    assert (experiment / "data/raw").is_dir()
    with pytest.raises(FileExistsError):
        create_experiment(experiment, "Other", "Other", ["Other"])


@pytest.mark.parametrize(
    "change",
    [
        {"title": " "},
        {"authors": []},
        {"authors": [""]},
        {"schema_version": "9"},
        {"created": "2026-01-01T00:00:00"},
    ],
)
def test_invalid_metadata(change):
    values = dict(title="T", description="D", authors=["A"])
    values.update(change)
    with pytest.raises(ValidationError):
        Manifest(**values)


def test_registration_checksum_and_roundtrip(experiment, tmp_path):
    source = tmp_path / "données.csv"
    source.write_bytes(b"x,y\n1,2\n")
    entry = add_file(experiment, source, Role.raw, "Dataset")
    assert entry.sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest(experiment / entry.path) == entry.sha256
    with pytest.raises(OpenReproError):
        add_file(experiment, source, Role.raw)
    first = export_experiment(experiment, tmp_path / "a.orepro")
    second = export_experiment(experiment, tmp_path / "b.orepro")
    assert first.read_bytes() == second.read_bytes()
    imported = import_experiment(first, tmp_path / "imported")
    assert load(imported) == load(experiment)
    assert (imported / entry.path).read_bytes() == source.read_bytes()
    assert validate_experiment(imported)["status"] == "PASS"
    with pytest.raises(OpenReproError):
        export_experiment(experiment, first)
    with pytest.raises(OpenReproError):
        import_experiment(first, imported)


@pytest.mark.parametrize(
    "corruption",
    ["missing", "modified", "extra", "crate", "json", "version", "duplicate", "relationship"],
)
def test_validation_failures(experiment, corruption):
    if corruption == "missing":
        (experiment / "README.md").unlink()
    elif corruption == "modified":
        (experiment / "README.md").write_text("tampered")
    elif corruption == "extra":
        (experiment / "unregistered").write_text("extra")
    elif corruption == "crate":
        (experiment / "ro-crate-metadata.json").write_text("{}")
    elif corruption == "json":
        (experiment / "manifest.json").write_text("{broken")
    elif corruption == "version":
        data = json.loads((experiment / "manifest.json").read_text())
        data["schema_version"] = "9"
        (experiment / "manifest.json").write_text(json.dumps(data))
    else:
        manifest = load(experiment)
        if corruption == "duplicate":
            manifest.files.append(manifest.files[0])
        else:
            manifest.files[0].derived_from = ["missing.csv"]
        save(experiment, manifest)
    assert validate_experiment(experiment)["status"] == "FAIL"


def test_warn_without_reproduction(tmp_path):
    root = tmp_path / "warning"
    create_experiment(root, "Study", "Synthetic", ["A"])
    assert validate_experiment(root)["status"] == "WARN"


def test_invalid_relation_does_not_copy(experiment, tmp_path):
    source = tmp_path / "x.txt"
    source.write_text("x")
    with pytest.raises(OpenReproError):
        add_file(experiment, source, Role.processed, derived_from=["absent"])
    assert not (experiment / "data/processed/x.txt").exists()


def test_reserved_and_uninventoried(experiment):
    manifest = load(experiment)
    manifest.files[0].path = "manifest.json"
    save(experiment, manifest)
    assert validate_experiment(experiment)["status"] == "FAIL"


def test_metadata_duplicate_keys(experiment):
    (experiment / "manifest.json").write_text('{"title":"A","title":"B"}')
    assert validate_experiment(experiment)["status"] == "FAIL"


def test_ro_crate_iri_paths(experiment, tmp_path):
    source = tmp_path / "données #1.csv"
    source.write_text("synthetic")
    entry = add_file(experiment, source, Role.raw)
    graph = json.loads((experiment / "ro-crate-metadata.json").read_text())["@graph"]
    assert any(node["@id"] == "data/raw/donn%C3%A9es%20%231.csv" for node in graph)
    assert entry.path == "data/raw/données #1.csv"
    assert validate_experiment(experiment)["status"] == "PASS"


@pytest.mark.parametrize("content", ["[]", "null", '{"events":[NaN]}'])
def test_invalid_provenance_json(experiment, content):
    from openrepro.experiments import digest

    path = experiment / "provenance/provenance.json"
    path.write_text(content)
    manifest = load(experiment)
    for entry in manifest.files:
        if entry.path == "provenance/provenance.json":
            entry.sha256 = digest(path)
            entry.size = path.stat().st_size
    save(experiment, manifest)
    assert validate_experiment(experiment)["status"] == "FAIL"
