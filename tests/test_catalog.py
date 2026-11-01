"""Immutable exchange, revision search, citations and a real read-only HTTP service."""

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from openrepro.catalog import (
    catalog_server,
    citation,
    fetch_package,
    package_path,
    publish_package,
    search_catalog,
)
from openrepro.experiments import create_experiment, update_metadata
from openrepro.models import OpenReproError
from openrepro.packages import export_experiment
from openrepro.validation import validate_experiment


@pytest.fixture
def published(tmp_path):
    root = tmp_path / "study"
    create_experiment(
        root, "<script>Dataset</script>", "Iris data", ["Researcher"], keywords=["biology"]
    )
    package = export_experiment(root, tmp_path / "study.orepro")
    catalog = tmp_path / "catalog"
    record = publish_package(package, catalog)
    return root, package, catalog, record


def test_immutable_exchange_and_versions(published, tmp_path):
    root, package, catalog, first = published
    assert first["revision"] == 1
    assert first["identifier"] == "urn:sha256:" + first["sha256"]
    assert publish_package(package, catalog) == first
    update_metadata(root, {"title": "Revised Iris"})
    second = publish_package(export_experiment(root, tmp_path / "second.orepro"), catalog)
    assert second["revision"] == 2
    assert second["sha256"] != first["sha256"]
    assert len(search_catalog(catalog, experiment=first["experiment"])) == 2
    assert search_catalog(catalog, "biology")
    assert search_catalog(catalog, "' OR 1=1 --") == []
    assert search_catalog(catalog, "%") == []
    received = tmp_path / "received"
    fetch_package(catalog, first["sha256"], received)
    assert validate_experiment(received)["status"] == "WARN"
    assert citation(catalog, first["sha256"])["id"] == first["identifier"]
    assert "DOI" not in citation(catalog, first["sha256"])


def test_catalog_detects_tampering(published):
    _, _, catalog, record = published
    blob = package_path(catalog, record["sha256"])
    blob.write_bytes(b"tampered")
    with pytest.raises(OpenReproError, match="integrity"):
        package_path(catalog, record["sha256"])


def test_read_only_http_catalog(published):
    _, package, catalog, record = published
    with catalog_server(catalog, port=0) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        try:
            with urllib.request.urlopen(base + "/search?q=biology") as response:
                values = json.load(response)
                assert values["packages"][0]["sha256"] == record["sha256"]
            with urllib.request.urlopen(
                base + "/packages/" + record["sha256"] + ".orepro"
            ) as response:
                assert response.read() == package.read_bytes()
                assert response.headers["ETag"] == '"' + record["sha256"] + '"'
            with urllib.request.urlopen(base + "/") as response:
                page = response.read().decode()
                assert "<script>Dataset</script>" not in page
                assert "&lt;script&gt;" in page
            for path in ("/packages/../catalog.sqlite3", "/execute", "/packages/not-a-hash"):
                with pytest.raises(urllib.error.HTTPError):
                    urllib.request.urlopen(base + path)
            with pytest.raises(urllib.error.HTTPError) as exc:
                urllib.request.urlopen(
                    urllib.request.Request(base + "/search", data=b"payload", method="POST")
                )
            assert exc.value.code == 501
        finally:
            server.shutdown()
            worker.join(timeout=5)


def test_partial_blob_copy_is_removed_and_publication_can_retry(tmp_path, monkeypatch):
    from openrepro import catalog as module

    root = tmp_path / "study"
    create_experiment(root, "Copy recovery", "D", ["A"])
    package = export_experiment(root, tmp_path / "study.orepro")
    catalog = tmp_path / "catalog"
    original = module.shutil.copyfileobj

    def interrupted(source, output, *args, **kwargs):
        if Path(output.name).parent == catalog / "packages":
            output.write(b"partial")
            raise OSError("Injected catalog copy failure")
        return original(source, output, *args, **kwargs)

    monkeypatch.setattr(module.shutil, "copyfileobj", interrupted)
    with pytest.raises(OSError, match="Injected catalog copy failure"):
        publish_package(package, catalog)
    assert not list((catalog / "packages").glob("*.orepro"))
    assert search_catalog(catalog) == []
    monkeypatch.setattr(module.shutil, "copyfileobj", original)
    record = publish_package(package, catalog)
    assert package_path(catalog, record["sha256"]).read_bytes() == package.read_bytes()


@pytest.mark.parametrize("fail", [False, True])
def test_catalog_connections_are_closed_after_commit_or_rollback(tmp_path, fail):
    import sqlite3

    from openrepro.catalog import database

    connection = None
    try:
        with database(tmp_path / "catalog") as connection:
            connection.execute("CREATE TABLE resource_check (value INTEGER)")
            connection.execute("INSERT INTO resource_check VALUES (1)")
            if fail:
                raise RuntimeError("cancel transaction")
    except RuntimeError:
        assert fail
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")
    with database(tmp_path / "catalog") as reopened:
        assert reopened.execute("SELECT COUNT(*) FROM resource_check").fetchone()[0] == (
            0 if fail else 1
        )
