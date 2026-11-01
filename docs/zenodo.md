# Zenodo deposit and DOI

Create a local deposit bundle from a validated research package:

```bash
openrepro deposit-bundle study.orepro --output deposit --json
```

The new directory contains `experiment.orepro`, `metadata.json`, `SHA256SUMS` and
review instructions. It has no DOI and performs no network operation. Review the
actual title, creators, description, license, access rights and resource type in the
metadata. Defaults describe a public dataset; change `upload_type` to `software`
for a software resource where appropriate. Possession of files does not confer the
right to publish third-party data or make private data public.

## Secure credentials and draft creation

Create a Zenodo personal token with the `deposit:write` and `deposit:actions` scopes.
Enter it as `ZENODO_ACCESS_TOKEN` through secure environment settings, never in chat,
command arguments, tracked files or metadata. Allow HTTPS to `zenodo.org`; API
metadata and upload bucket links remain on that exact host. The cloud configuration
draft declares this binding; saving a requirement does not supply its value or apply
network access. Review/save environment settings before retrying a blocked request.

```bash
openrepro zenodo-deposit deposit --json
```

This creates/resumes a draft and verifies the upload's size and Zenodo-provided MD5
transport checksum. The package's SHA-256 remains the local content identity. The
client retains system TLS verification, uses bearer headers and refuses redirects
or bucket links to another host. Proxy-bound tokens work through their configured
HTTPS destination. No token is written to the local journal.

## Publish and resume

After reviewing the draft and metadata:

```bash
openrepro zenodo-deposit deposit --publish --json
```

Publication makes the reviewed record public and can register a persistent DOI.
The client reports `published` and a DOI only after a confirming API response;
a draft or reserved DOI is not a published record. Published-record reconciliation
checks that its file checksum/size matches the local bundle. A journal records the
deposition ID and progress, so retries use the same draft rather than creating
another record.

If creation times out before its ID is received, the journal remains `creating`.
Find the actual draft in your Zenodo account and resume with
`--deposition-id THE_ACTUAL_ID`. The client refuses to guess or create another draft.
A lost publication response is reconciled by reading the same record on retry.
Do not delete `zenodo.json` to work around an uncertain outcome. Metadata/package
changes after deposit require a new reviewed bundle; do not silently replace an
existing published record. Use Zenodo's versioning workflow for subsequent releases.

The integration follows the [official Zenodo API documentation](https://developers.zenodo.org/).
Contract tests exercise draft/publication/retry/error paths without a real token.
Those tests are not evidence of a successful live deposit. Live DOI registration
remains blocked until the credential and destination access are actually available.
