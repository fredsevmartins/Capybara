"""Resumable Zenodo deposits; credentials never enter journals or URL parameters."""

import hashlib
import html
import os
import re
import shutil
import ssl
import tempfile
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx

from .experiments import atomic_write, digest, json_bytes, load, load_json
from .models import OpenReproError
from .packages import import_experiment

API = "https://zenodo.org/api/deposit/depositions"


def deposit_bundle(package: Path, destination: Path) -> dict:
    package, destination = Path(package), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise OpenReproError("Deposit destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".openrepro-deposit-", dir=destination.parent
    ) as directory:
        staging = Path(directory)
        copied = staging / "experiment.orepro"
        shutil.copyfile(package, copied)
        root = import_experiment(copied, staging / "verified")
        manifest = load(root)
        metadata = {
            "title": manifest.title,
            "description": html.escape(manifest.description),
            "upload_type": "dataset",
            "creators": [{"name": name} for name in manifest.authors],
            "access_right": "open",
            "license": manifest.license.lower(),
            "keywords": manifest.keywords,
        }
        (staging / "metadata.json").write_bytes(json_bytes({"metadata": metadata}))
        checksum = digest(copied)
        (staging / "SHA256SUMS").write_text(checksum + "  experiment.orepro\n", encoding="utf-8")
        (staging / "README.txt").write_text(
            "Review authors, license, rights and metadata before depositing.\n"
            "This bundle is local; it has no assigned DOI.\n"
            "Use openrepro zenodo-deposit BUNDLE to create/resume a draft.\n"
            "Use --publish only when ready for irreversible public publication.\n",
            encoding="utf-8",
        )
        shutil.rmtree(root)
        staging.rename(destination)
    return {"bundle": str(destination), "sha256": checksum, "status": "LOCAL_ONLY", "doi": None}


def _bucket_url(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "zenodo.org"
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
        or not re.fullmatch(r"/api/files/[A-Za-z0-9-]+", parsed.path)
    ):
        raise OpenReproError("Zenodo returned an unsafe bucket URL")
    return value.rstrip("/")


def _request(client, method, url, **kwargs):
    try:
        response = client.request(method, url, follow_redirects=False, **kwargs)
        response.raise_for_status()
        if len(response.content) > 4 * 1024 * 1024:
            raise OpenReproError("Zenodo response exceeds metadata limit")
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenReproError(
            "Zenodo request failed; check access, metadata and saved deposit journal"
        ) from exc


def zenodo_deposit(
    bundle: Path, *, publish=False, deposition_id: int | None = None, client=None
) -> dict:
    """Create/resume a draft; publication requires an explicit separate flag."""
    token = os.environ.get("ZENODO_ACCESS_TOKEN")
    if not token:
        raise OpenReproError("Configure ZENODO_ACCESS_TOKEN securely in environment settings")
    bundle = Path(bundle)
    package = bundle / "experiment.orepro"
    metadata = load_json(bundle / "metadata.json")
    checksum = digest(package)
    # Validate before any remote write, including externally edited bundles.
    with tempfile.TemporaryDirectory() as directory:
        import_experiment(package, Path(directory) / "verified")
    expected = (bundle / "SHA256SUMS").read_text(encoding="utf-8").split()
    if expected != [checksum, "experiment.orepro"]:
        raise OpenReproError("Deposit bundle checksum mismatch")
    with package.open("rb") as stream:
        local_md5 = hashlib.file_digest(
            stream, lambda: hashlib.md5(usedforsecurity=False)
        ).hexdigest()
    journal_path = bundle / "zenodo.json"
    journal = (
        load_json(journal_path) if journal_path.exists() else {"sha256": checksum, "state": "new"}
    )
    metadata_hash = hashlib.sha256(json_bytes(metadata)).hexdigest()
    if (
        journal["sha256"] != checksum
        or journal.get("metadata_sha256", metadata_hash) != metadata_hash
    ):
        raise OpenReproError("Deposit package/metadata differs from the saved journal")
    journal["metadata_sha256"] = metadata_hash
    if journal.get("state") == "published":
        return journal
    if deposition_id is not None:
        if deposition_id < 1 or journal.get("id", deposition_id) != deposition_id:
            raise OpenReproError("Invalid or conflicting deposition ID")
        journal["id"] = deposition_id
        journal["state"] = "draft"
        atomic_write(journal_path, json_bytes(journal))
    if journal.get("state") == "creating" and "id" not in journal:
        raise OpenReproError(
            "Creation outcome unknown; locate the draft in Zenodo and pass its deposition ID"
        )
    owned_client = client is None
    if client is None:
        client = httpx.Client(
            verify=ssl.create_default_context(),
            follow_redirects=False,
            timeout=120,
            headers={"Authorization": "Bearer " + token},
        )
    try:
        if "id" not in journal:
            journal["state"] = "creating"
            atomic_write(journal_path, json_bytes(journal))
            created = _request(client, "POST", API, json={})
            identifier = created.get("id")
            if not isinstance(identifier, int) or identifier < 1:
                raise OpenReproError("Zenodo returned an invalid deposition ID")
            journal.update(id=identifier, state="draft")
            atomic_write(journal_path, json_bytes(journal))
        url = API + "/" + str(journal["id"])
        remote = _request(client, "GET", url)
        if remote.get("submitted"):
            files = _request(client, "GET", url + "/files")
            if not any(
                item.get("filename") == "experiment.orepro"
                and item.get("checksum", "").removeprefix("md5:") == local_md5
                and item.get("filesize") == package.stat().st_size
                for item in files
            ):
                raise OpenReproError("Published record does not match this deposit bundle")
            doi = remote.get("doi") or remote.get("metadata", {}).get("doi")
            if not doi:
                raise OpenReproError("Published deposition has no confirmed DOI")
            journal.update(
                state="published", doi=doi, record_url="https://doi.org/" + quote(doi, safe="/")
            )
            atomic_write(journal_path, json_bytes(journal))
            return journal
        bucket = _bucket_url(remote.get("links", {}).get("bucket", ""))
        _request(client, "PUT", url, json=metadata)
        with package.open("rb") as stream:
            uploaded = _request(
                client,
                "PUT",
                bucket + "/experiment.orepro",
                content=stream,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(package.stat().st_size),
                },
            )
        # Zenodo's file API supplies MD5; SHA-256 remains our content identity.
        if (
            uploaded.get("checksum", "").removeprefix("md5:") != local_md5
            or uploaded.get("size") != package.stat().st_size
        ):
            raise OpenReproError("Zenodo upload checksum/size mismatch; draft not published")
        journal.update(
            state="draft",
            upload_verified=True,
            draft_url="https://zenodo.org/deposit/" + str(journal["id"]),
        )
        atomic_write(journal_path, json_bytes(journal))
        if publish:
            # Persist before POST: a timeout must not cause a new draft or duplicate publication.
            journal["state"] = "publishing"
            atomic_write(journal_path, json_bytes(journal))
            _request(client, "POST", url + "/actions/publish")
            confirmed = _request(client, "GET", url)
            doi = confirmed.get("doi") or confirmed.get("metadata", {}).get("doi")
            if not confirmed.get("submitted") or not doi:
                raise OpenReproError("Publication not confirmed; retry using the saved journal")
            journal.update(
                state="published", doi=doi, record_url="https://doi.org/" + quote(doi, safe="/")
            )
            atomic_write(journal_path, json_bytes(journal))
        return journal
    finally:
        if owned_client:
            client.close()
