# Troubleshooting

- **Destination exists:** use a fresh workspace/export name. OpenRepro never silently
  replaces an existing package or registered file.
- **FAIL checksum/inventory:** restore the original file or register a separately named
  revised file in a valid workspace. Do not rewrite recorded hashes to hide corruption.
- **WARN reproduction:** add meaningful reproduction instructions through metadata
  management; see [Python API](python-api.md).
- **Invalid RO-Crate:** v0.1 accepts its strict generated profile; arbitrary RO-Crates
  with additional entities need a conversion workflow, not forced import.
- **Resource limit:** large or exceptionally compressed archives may exceed the limits
  in the format specification. Do not bypass checks for untrusted input.
- **MCP waits silently:** stdio expects a client to initialize the protocol; it is not
  an interactive shell or HTTP server. Check absolute executable and workspace paths.
- **MCP invalid path:** all tool paths must be relative and inside the configured root.
- **Missing command:** activate `.venv` and install with `python -m pip install -e '.[dev]'`.
- **Example destination exists:** choose another `--output` directory to preserve files.

Report exact commands, versions and sanitized errors; never attach private research
files or credentials without review.
