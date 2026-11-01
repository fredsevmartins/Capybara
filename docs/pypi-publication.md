# Publish the candidate on PyPI through GitHub

The Zenodo DOI is separate from Python package distribution. PyPI needs no Zenodo
token. The configured release workflow uses short-lived GitHub OIDC, not a token
pasted into chat or repository files.

## Account and pending publisher

Create/sign into [PyPI](https://pypi.org/account/register/), verify the account email
and enable PyPI-required two-factor authentication. In account settings open
[Publishing](https://pypi.org/manage/account/publishing/) and add a **pending publisher**
for a new project. The public `openrepro` project endpoint returned 404 at inspection;
that does not reserve the name or establish ownership.

Select GitHub and use:

| Field | Value |
| --- | --- |
| PyPI project name | `openrepro` |
| GitHub owner | `fredsevmartins` |
| GitHub repository | `Capybara` |
| Workflow filename | `release.yml` |
| Environment name | `pypi` |

If the project already exists, its owner must configure the publisher in that project's
Publishing settings instead. Do not overwrite someone else's package or guess credentials.
The workflow uses the matching `pypi` GitHub environment and scoped `id-token: write`.
Configure any desired approval protection in that environment before the run.

## Verify and publish

First confirm the corrected OS/Python CI matrix succeeds. Then use GitHub Actions
workflow **release → Run workflow**, select the verified candidate tag's version
without `v`, and enable `publish_pypi` only after the pending publisher is configured.
The workflow checks source version, lint/docs/tests, builds artifacts and verifies
metadata/inventories before upload. A failed verification blocks its publish job.
An existing DOI/tag alone does not establish these checks passed.

After publication, verify the PyPI page and a clean installation, for example:

```bash
python -m pip install 'openrepro==1.0.0rc2'
openrepro version --json
```

The command is an acceptance check after confirmed upload, not a claim that the
package is already available. Release candidates may require an explicit version
or `--pre`; do not advertise final 1.0 availability prematurely. Preserve existing
immutable tags and published Zenodo files. A new code revision gets a new version.
