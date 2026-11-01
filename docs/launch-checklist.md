# Release acceptance and external gates

This file distinguishes implemented engineering work from acceptance that requires
outside evidence. `1.0.0rc1` is a candidate, not a declaration that every final-product
gate has been satisfied.

| Stage | Engineering delivered | Acceptance still required |
| --- | --- | --- |
| 1. Reproducible environments | Binary resolution, exact hashes, registered lock/wheels, offline image build/cache, combined build/run | Representative user studies beyond the supplied cases |
| 2. Execution reliability | Real tmpfs quota, no writable host mounts, bounded safe collection, timeout/cleanup, labelled recovery journals | Independent security review appropriate to the deployment threat model |
| 3. Scientific evidence | Attributed real Iris measurements, independently implemented numerical references, units and justified tolerances | Independent researchers assessing real methods and new datasets |
| 4. Researcher workflow | Recipe assistance, doctor, readable reports, complete CLI/API documentation | Usability feedback from researchers completing the workflow independently |
| 5. Public sharing | Immutable revisions, search, content identities, citations, read-only catalog, resumable Zenodo integration | Real Zenodo token/access, reviewed metadata and confirmed published DOI |
| 6. Release preparation | Native-package regression tests, schemas, supported API, RO-Crate conversion, Python/shell execution, release artifacts and OIDC workflow | Successful remote CI matrix, PyPI project ownership/trusted publisher, actual distribution and restored-environment validation |

## Publishing credentials and infrastructure

The actual cloud configuration had no Zenodo or PyPI credential binding at inspection.
`ZENODO_ACCESS_TOKEN` and HTTPS access to `zenodo.org` were requested through the
configuration draft. Add the token securely and save/review the allowed domains;
never supply token values in chat. The draft also requests `api.github.com` for
release/CI visibility and `upload.pypi.org` for distribution. A saved requirement is
not a ready credential or an applied network policy.

For PyPI, establish ownership of `openrepro`, configure a trusted publisher for
`fredsevmartins/OpenRepro`, workflow `release.yml`, environment `pypi`, then run the
manual workflow against a verified tag with `publish_pypi` enabled. It uses scoped
OIDC, not a committed API token. The workflow builds and verifies artifacts first.
Do not claim a package is available on PyPI until upload and clean installation
have actually succeeded.

For Zenodo, prepare a local deposit bundle, review licensing/authorship/resource
type, create a draft, then explicitly publish. Confirm the returned public DOI.
The existing source Iris DOI must never be presented as a DOI assigned to this
software or a newly generated package.

## Final 1.0 decision

Run the local validation and artifact checks, inspect the remote OS/Python matrix,
complete independent scientific/usability acceptance, perform a security review
for the intended deployment, publish the distribution and DOI, then validate an
installation on another machine. Record actual URLs, versions, outcomes and limitations
in the verification report. Until then keep the release-candidate designation.
