"""Zenodo protocol contract tests; no live account, token or publication is used."""

import hashlib
import json

import httpx
import pytest

from openrepro.experiments import create_experiment
from openrepro.models import OpenReproError
from openrepro.packages import export_experiment
from openrepro.zenodo import API, deposit_bundle, zenodo_deposit


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "study"
    create_experiment(root, "Study", "<b>Plain research description</b>", ["Researcher"])
    package = export_experiment(root, tmp_path / "study.orepro")
    directory = tmp_path / "deposit"
    result = deposit_bundle(package, directory)
    assert result["doi"] is None
    assert result["status"] == "LOCAL_ONLY"
    return directory


def zenodo_service(bundle, *, corrupt=False, unsafe_bucket=False, lose_publish_response=False):
    state = {"created": 0, "submitted": False, "uploaded": None, "calls": [], "lost": False}
    local = (bundle / "experiment.orepro").read_bytes()
    checksum = hashlib.md5(local, usedforsecurity=False).hexdigest()

    def handler(request):
        assert request.url.host == "zenodo.org"
        assert request.url.scheme == "https"
        assert "access_token" not in str(request.url)
        assert request.headers["authorization"] == "Bearer synthetic-test-token"
        path = request.url.path
        state["calls"].append((request.method, path))
        if request.method == "POST" and path == "/api/deposit/depositions":
            state["created"] += 1
            return httpx.Response(201, json={"id": 42})
        if request.method == "GET" and path.endswith("/files"):
            return httpx.Response(
                200,
                json=[
                    {"filename": "experiment.orepro", "filesize": len(local), "checksum": checksum}
                ],
            )
        if request.method == "GET" and path == "/api/deposit/depositions/42":
            remote = {
                "id": 42,
                "submitted": state["submitted"],
                "links": {
                    "bucket": "https://evil.example/api/files/bucket"
                    if unsafe_bucket
                    else "https://zenodo.org/api/files/known-bucket"
                },
                "metadata": {},
            }
            if state["submitted"]:
                remote["doi"] = "10.5281/zenodo.42"
            return httpx.Response(200, json=remote)
        if request.method == "PUT" and path == "/api/deposit/depositions/42":
            state["metadata"] = json.loads(request.read())
            return httpx.Response(200, json={"id": 42})
        if request.method == "PUT" and path == "/api/files/known-bucket/experiment.orepro":
            state["uploaded"] = request.read()
            assert state["uploaded"] == local
            return httpx.Response(
                200,
                json={"size": len(local), "checksum": "md5:" + ("0" * 32 if corrupt else checksum)},
            )
        if request.method == "POST" and path.endswith("/actions/publish"):
            state["submitted"] = True
            if lose_publish_response and not state["lost"]:
                state["lost"] = True
                raise httpx.ReadTimeout("simulated lost response")
            return httpx.Response(202, json={"id": 42})
        raise AssertionError((request.method, path))

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer synthetic-test-token"},
    )
    return client, state


def test_missing_token_performs_no_remote_write(bundle, monkeypatch):
    monkeypatch.delenv("ZENODO_ACCESS_TOKEN", raising=False)
    with pytest.raises(OpenReproError, match="securely"):
        zenodo_deposit(bundle)
    assert not (bundle / "zenodo.json").exists()


def test_draft_then_confirmed_publication_is_resumable(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")
    client, state = zenodo_service(bundle)
    with client:
        draft = zenodo_deposit(bundle, client=client)
        assert draft["state"] == "draft"
        assert "doi" not in draft
        assert not state["submitted"]
        published = zenodo_deposit(bundle, publish=True, client=client)
        assert published["state"] == "published"
        assert published["doi"] == "10.5281/zenodo.42"
        assert state["created"] == 1
        assert zenodo_deposit(bundle, publish=True, client=client) == published
    assert "synthetic-test-token" not in (bundle / "zenodo.json").read_text()
    assert "&lt;b&gt;" in state["metadata"]["metadata"]["description"]


def test_wrong_remote_checksum_cannot_publish(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")
    client, state = zenodo_service(bundle, corrupt=True)
    with client, pytest.raises(OpenReproError, match="checksum"):
        zenodo_deposit(bundle, publish=True, client=client)
    assert not state["submitted"]


def test_server_links_cannot_leak_auth_to_another_host(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")
    client, state = zenodo_service(bundle, unsafe_bucket=True)
    with client, pytest.raises(OpenReproError, match="unsafe bucket"):
        zenodo_deposit(bundle, publish=True, client=client)
    assert state["uploaded"] is None


def test_lost_publish_response_does_not_duplicate_deposit(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")
    client, state = zenodo_service(bundle, lose_publish_response=True)
    with client:
        with pytest.raises(OpenReproError, match="request failed"):
            zenodo_deposit(bundle, publish=True, client=client)
        result = zenodo_deposit(bundle, publish=True, client=client)
        assert result["state"] == "published"
        assert state["created"] == 1
        assert sum(path.endswith("/actions/publish") for _, path in state["calls"]) == 1


def test_uncertain_creation_requires_reconciliation(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")

    def handler(request):
        assert str(request.url) == API
        raise httpx.ReadTimeout("unknown creation outcome")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OpenReproError, match="request failed"):
            zenodo_deposit(bundle, client=client)
        with pytest.raises(OpenReproError, match="Creation outcome unknown"):
            zenodo_deposit(bundle, client=client)


def test_modified_bundle_is_rejected_before_network(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")
    (bundle / "SHA256SUMS").write_text("0" * 64 + "  experiment.orepro\n")
    with pytest.raises(OpenReproError, match="checksum mismatch"):
        zenodo_deposit(bundle)


def test_existing_published_record_must_match_bundle(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")

    def handler(request):
        if request.url.path.endswith("/files"):
            return httpx.Response(
                200, json=[{"filename": "other.zip", "filesize": 1, "checksum": "0" * 32}]
            )
        return httpx.Response(200, json={"submitted": True, "doi": "10.5281/zenodo.99"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OpenReproError, match="does not match"):
            zenodo_deposit(bundle, deposition_id=99, client=client)
    assert json.loads((bundle / "zenodo.json").read_text())["id"] == 99


def test_cached_publication_is_reconciled_with_remote_record(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")
    client, state = zenodo_service(bundle)
    with client:
        zenodo_deposit(bundle, publish=True, client=client)
    state_calls = []

    def wrong_record(request):
        state_calls.append(request.url.path)
        if request.url.path.endswith("/files"):
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={"submitted": True, "doi": "10.5281/zenodo.42"})

    with httpx.Client(transport=httpx.MockTransport(wrong_record)) as changed:
        with pytest.raises(OpenReproError, match="does not match"):
            zenodo_deposit(bundle, client=changed)
    assert len(state_calls) == 2


@pytest.mark.parametrize("identifier", [True, False, 0, -1, "42", "../record"])
def test_invalid_saved_deposition_id_performs_no_network(bundle, monkeypatch, identifier):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")
    checksum = hashlib.sha256((bundle / "experiment.orepro").read_bytes()).hexdigest()
    (bundle / "zenodo.json").write_text(
        json.dumps(
            {"sha256": checksum, "state": "published", "id": identifier, "doi": "10.5281/zenodo.42"}
        )
    )

    def unexpected(request):
        raise AssertionError("Invalid journal must not reach the network")

    with httpx.Client(transport=httpx.MockTransport(unexpected)) as client:
        with pytest.raises(OpenReproError, match="Invalid deposition ID"):
            zenodo_deposit(bundle, client=client)


def test_malformed_remote_json_keeps_creation_outcome_uncertain(bundle, monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "synthetic-test-token")
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(201, json=[]))
    ) as client:
        with pytest.raises(OpenReproError, match="unexpected response structure"):
            zenodo_deposit(bundle, client=client)
    assert json.loads((bundle / "zenodo.json").read_text())["state"] == "creating"
