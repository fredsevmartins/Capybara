# Changelog

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
