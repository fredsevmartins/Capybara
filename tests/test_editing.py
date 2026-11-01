"""Editing, provenance and fault-injection regression tests."""

import json

import pytest

from openrepro import experiments as api
from openrepro.models import OpenReproError, Role
from openrepro.packages import export_experiment, import_experiment
from openrepro.validation import validate_experiment


@pytest.fixture
def study(tmp_path):
    root = tmp_path / "study"
    api.create_experiment(root, "Study", "Description", ["A"], reproduction="Read protocol")
    return root


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def events(root):
    return api.load_json(root / api.PROVENANCE)["events"]


@pytest.mark.parametrize("operation", ["add", "replace", "remove", "update"])
@pytest.mark.parametrize("failure", ["save", "partial_save", "event"])
def test_failed_edit_preserves_original_bytes(study, tmp_path, monkeypatch, operation, failure):
    source = tmp_path / "data.csv"
    source.write_text("x\n1\n")
    entry = api.add_file(study, source, Role.raw)
    replacement = tmp_path / "replacement.csv"
    replacement.write_text("x\n2\n")
    before = snapshot(study)
    original_save = api.save

    def fail(*args, **kwargs):
        raise OSError("Injected write failure")

    def partial_save(root, manifest):
        api.atomic_write(root / "ro-crate-metadata.json", api.json_bytes(api.crate(manifest)))
        fail()

    if failure == "event":
        monkeypatch.setattr(api, "record_event", fail)
    elif failure == "partial_save":
        monkeypatch.setattr(api, "save", partial_save)
    else:
        monkeypatch.setattr(api, "save", fail)
    with pytest.raises(OSError, match="Injected"):
        if operation == "add":
            api.add_file(study, replacement, Role.raw)
        elif operation == "replace":
            api.replace_file(study, entry.path, replacement)
        elif operation == "remove":
            api.remove_file(study, entry.path)
        else:
            api.update_metadata(study, {"title": "Changed"})
    monkeypatch.setattr(api, "save", original_save)
    assert snapshot(study) == before
    assert validate_experiment(study)["status"] == "PASS"
    assert not list(tmp_path.glob(".openrepro-backup-*"))


def test_editing_roundtrip_and_history(study, tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("x\n1\n")
    identifier = api.load(study).identifier
    entry = api.add_file(study, source, Role.raw)
    old_hash = entry.sha256
    source.write_text("x\n2\n")
    entry = api.replace_file(study, entry.path, source)
    assert entry.sha256 != old_hash
    updated = api.update_metadata(study, {"title": "Updated", "doi": "10.1234/example"})
    assert updated.identifier == identifier
    assert events(study)[-2]["previous_sha256"] == old_hash
    assert events(study)[-1]["fields"] == ["doi", "title"]
    api.remove_file(study, entry.path)
    assert not (study / entry.path).exists()
    assert [e["action"] for e in events(study)] == [
        "create",
        "add",
        "replace",
        "update_metadata",
        "remove",
    ]
    package = export_experiment(study, tmp_path / "study.orepro")
    restored = import_experiment(package, tmp_path / "restored")
    assert snapshot(restored) == snapshot(study)
    assert validate_experiment(restored)["status"] == "PASS"


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"identifier": "abc"},
        {"files": []},
        {"created": "2026-01-01"},
        {"title": " "},
        {"authors": []},
        {"experimental_date": "invalid"},
    ],
)
def test_invalid_metadata_is_nonmutating(study, changes):
    before = snapshot(study)
    with pytest.raises(ValueError):
        api.update_metadata(study, changes)
    assert snapshot(study) == before


def test_dependencies_and_required_documents(study, tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("x")
    raw = api.add_file(study, source, Role.raw)
    derived = api.add_file(study, source, Role.processed, derived_from=[raw.path])
    before = snapshot(study)
    for action in (
        lambda: api.remove_file(study, raw.path),
        lambda: api.replace_file(study, raw.path, source),
        lambda: api.remove_file(study, "README.md"),
        lambda: api.remove_file(study, api.PROVENANCE),
        lambda: api.replace_file(study, api.PROVENANCE, source),
        lambda: api.remove_file(study, "../outside"),
    ):
        with pytest.raises(OpenReproError):
            action()
        assert snapshot(study) == before
    api.remove_file(study, derived.path)
    api.remove_file(study, raw.path)
    assert validate_experiment(study)["status"] == "PASS"


def test_partial_copy_is_rolled_back(study, tmp_path, monkeypatch):
    source = tmp_path / "data.csv"
    source.write_text("data")
    before = snapshot(study)

    def fail_copy(input_file, output):
        output.write(b"partial")
        raise OSError("Copy interrupted")

    monkeypatch.setattr(api.shutil, "copyfileobj", fail_copy)
    with pytest.raises(OSError, match="Copy interrupted"):
        api.add_file(study, source, Role.raw)
    assert snapshot(study) == before


def test_cli_editing(tmp_path):
    from test_interfaces import cli

    root = tmp_path / "exp"
    cli("init", root, "--title", "T", "--description", "D", "--author", "A", "--json")
    source = tmp_path / "data.csv"
    source.write_text("first")
    cli("add", root, source, "--role", "raw", "--json")
    source.write_text("second")
    cli("replace", root, "data/raw/data.csv", source, "--json")
    changes = tmp_path / "changes.json"
    changes.write_text(json.dumps({"title": "Changed", "reproduction": "Read protocol"}))
    assert cli("update", root, "--metadata", changes, "--json")["title"] == "Changed"
    cli("remove", root, "data/raw/data.csv", "--json")
    assert cli("validate", root, "--json")["status"] == "PASS"
    cli("remove", root, "README.md", "--json", expected=2)


def test_failed_rollback_keeps_recovery_files(study, tmp_path, monkeypatch):
    source = tmp_path / "data.csv"
    source.write_text("data")

    def fail(*args, **kwargs):
        raise OSError("Storage unavailable")

    monkeypatch.setattr(api, "record_event", fail)
    monkeypatch.setattr(api.os, "replace", fail)
    with pytest.raises(OpenReproError, match="recovery files retained"):
        api.add_file(study, source, Role.raw)
    backups = list(tmp_path.glob(".openrepro-backup-*"))
    assert len(backups) == 1
    recovery = api.load_json(backups[0] / "recovery.json")
    assert recovery["workspace"] == str(study)
    assert "manifest.json" in recovery["originals"]
    assert (backups[0] / str(recovery["paths"].index("manifest.json"))).is_file()
