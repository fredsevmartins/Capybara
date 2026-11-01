"""Immutable exchange, revision search, citations and a real read-only HTTP service."""

import json
import threading
import urllib.error
import urllib.request

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
