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
metadata and upload bucket links remain on that exact host. Configure this in your own execution environment. Declaring a variable name
is separate from securely supplying its value; check actual network access before
retrying a blocked request.

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
Those tests are not evidence of a successful live deposit. A live API deposit requires actual credentials and destination access. The project
also has a manually published record, described below; automated tests are separate
from that publication evidence.


## Manual upload and GitHub integration

You may publish through the Zenodo web interface without configuring an API token:

1. Log in at [Zenodo](https://zenodo.org/) and choose **New upload**.
2. Upload the reviewed release archive or research package. Choose the correct
   resource type, title, authors, description, license and publication date.
3. Select **No, I need one** if this resource has no DOI. Reserving a DOI can help
   prepare metadata, but registration/public availability happens on publication.
4. Save the draft, inspect its preview, then publish when the files and rights are
   correct. Confirm the public record URL and version DOI.
5. Keep the receipt/record URL and archive identity with your research records.

For future GitHub software releases, open your Zenodo account's **GitHub** settings,
connect/authorize GitHub, sync repositories and enable `fredsevmartins/Capybara`.
A subsequent stable GitHub Release can trigger archiving. Pre-releases may be ignored;
existing old releases are not evidence of a new deposit. Check the actual Zenodo
record before advertising a DOI. Avoid duplicate manual and automatic deposits
for the same intended version; use Zenodo's new-version workflow where appropriate.

## Cite the right record

The project concept DOI is [10.5281/zenodo.23869678](https://doi.org/10.5281/zenodo.23869678).
The user manually published a record titled OpenRepro 1.0.0rc1 with version DOI
[10.5281/zenodo.23869679](https://doi.org/10.5281/zenodo.23869679). Its uploaded file
is `OpenRepro-main.zip`; exact correspondence against the rc1 tag remains unverified.
The stable 1.0.0 GitHub release is a later revision. Do not reuse the rc1 version DOI
as proof of a 1.0.0 deposit. See [verification evidence](verification.md).

A concept DOI represents the version family; a version DOI identifies one archived
record. Choose the identifier that matches the work actually used. `CITATION.cff`
contains the project citation metadata, and `openrepro cite` emits experiment
citations from the local catalog. Declaring a DOI in metadata does not itself
register, verify ownership of or publish that identifier.
