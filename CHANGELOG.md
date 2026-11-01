# Changelog

## 1.0.0rc2 — candidate

- Rename the GitHub repository to Capybara; preserve OpenRepro package/CLI and published artifacts.

- Add Repro, an original capybara scientist mascot, with transparent artwork and brand usage documentation.
- Make interrupted catalog copies clean up only after file handles close, including Windows.
- Preserve JUnit outcomes and expose safe CI failure summaries without masking failed tests.

- Resolve explicitly selected parent-directory aliases without accepting direct or internal symlinks.
- Make RO-Crate test metadata describe actual LF/CRLF file sizes; preserve mismatch rejection.
- Register the manually published project DOI and distinguish the rc1 record from later code.
- Document PyPI trusted publication and verify the remote cross-platform matrix before promotion.

## 1.0.0rc1 — candidate (not final acceptance)

- Resolve binary Python dependencies into registered exact hash locks and wheelhouses;
  build/reuse offline environments and combine build with explicit reproduction.
- Enforce real tmpfs output quotas without writable host mounts; bound safe tar
  collection and recover labelled runs after abrupt runner termination.
- Add quantity units, justified tolerances and bounded difference diagnostics.
- Add attributed historical Iris measurements and independent numerical references.
- Add recipe assistance, runtime diagnostics and standalone HTML reports.
- Add immutable research catalog revisions, metadata search, verified downloads,
  citations and a read-only HTTP interface.
- Add local deposit bundles and resumable, explicitly published Zenodo deposits.
- Add explicit local RO-Crate conversion, published JSON schemas and supported API.
- Prepare verified distributions and an OIDC PyPI release workflow; external
  scientific/usability/security review, remote CI and live publication remain gates.

## 0.2.0.dev0 — 2026-11-01 (pre-release)

- Add validated reproduction recipes and CLI `plan`, `reproduce` and `compare` commands.
- Run reviewed code in a preloaded immutable Linux Docker image with no network,
  read-only inputs, non-root identity and resource limits; require explicit opt-in.
- Record image identity/platform, dependency-file hashes, recipe hash and run status.
- Compare exact bytes or nested numeric JSON with explicit tolerances and strict parsing.
- Add a dependency-free packaged analysis example, real Docker tests and a Linux CI job.
- Keep package schema 0.1 and the eleven management-only MCP tools compatible.

## 0.1.1 — 2026-11-01

- Add transactional file registration, payload replacement/removal and metadata updates.
- Restore affected workspace bytes after handled edit failures; retain recovery files
  if restoration fails.
- Record editing provenance with timestamps, field names and payload hashes.
- Prevent removal of required documents and edits to inputs with registered dependents.
- Expose editing through CLI, Python and three additional local MCP tools.
- Add fault-injection, editing lifecycle, dependency protection and interface tests.

## 0.1.0 — 2026-10-29

Initial implementation: versioned manifest, RO-Crate profile, workspaces, registration,
SHA-256 integrity, deterministic export, bounded ZIP import, CLI, local MCP server,
synthetic scientific demonstrations, tests and documentation.

Publication and CI status must be checked in the verification report and on GitHub.
