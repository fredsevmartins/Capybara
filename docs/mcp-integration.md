# MCP integration

The official Python MCP SDK supplies a stdio server. Start with:

```bash
openrepro-mcp --workspace experiments
```

A stdio process waits for a client; no web server or API key is involved.
A compatible local client's configuration can use this complete JSON example
(replace the two absolute paths with your installation and workspace):

```json
{
  "mcpServers": {
    "openrepro": {
      "command": "/absolute/path/OpenRepro/.venv/bin/openrepro-mcp",
      "args": ["--workspace", "/absolute/path/research"]
    }
  }
}
```

On Windows use the executable under `.venv/Scripts/`. Client configuration formats
can differ; the above uses the common `mcpServers` convention, not a universal standard.

Tools: `create_experiment`, `add_experiment_file`, `list_experiments`,
`inspect_experiment`, `validate_experiment`, `export_experiment`, `import_experiment`,
`list_experiment_files`, `update_experiment_metadata`, `replace_experiment_file`,
`remove_experiment_file`. Tool annotations generate validated JSON schemas; successful
calls return `{ "ok": true, "result": ... }`. Operational errors return a sanitized
`ok: false` result; schema errors are MCP errors. File roles are enumerated.

All tool paths are relative to the configured root, including source files, packages
and exports. Copy external input files into this trusted root yourself first. Import
destinations must be new. Do not set the root to an entire home directory.

ChatGPT's hosted connector mechanisms are not verified against this local stdio server.
Do not paste this configuration into a hosted connector or assume it can reach local
files. Use a local MCP-capable client; ChatGPT integration would require a separately
reviewed supported transport/deployment. No public endpoint is implemented in v0.1.

`tests/test_interfaces.py::test_real_mcp_stdio` initializes an actual SDK client,
lists all eleven tools and exercises their calls over stdio. [Interaction diagram](diagrams/mcp.md).

Editing tool arguments:

- `update_experiment_metadata(path, changes)`: an object of editable metadata fields.
- `replace_experiment_file(path, file, source)`: experiment path, registered relative
  payload path and replacement source relative to the configured MCP root.
- `remove_experiment_file(path, file)`: experiment and registered relative payload path.

Editing follows the same provenance, dependency protection and rollback rules as the
CLI and Python API. See [editing and recovery](editing.md).

The v0.2 development execution/comparison commands are CLI/Python-only. No MCP tool
starts containers, pulls images or runs scripts; the eleven management tools remain
unchanged. Use the explicit reviewed [execution workflow](execution.md) separately.
