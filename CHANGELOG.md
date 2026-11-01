# Changelog

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
