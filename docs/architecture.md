# Architecture

`models.py` defines Pydantic manifest fields, role names and portable paths.
`experiments.py` creates workspaces, copies files, hashes bytes and generates JSON-LD.
`validation.py` checks inventory, checksums and cross-document agreement.
`packages.py` exports normalized ZIP archives and validates staged imports before
renaming them into place. `cli.py` and `mcp_server.py` call these same functions.

State is stored in ordinary files. Metadata writes use atomic replacement per file;
validation detects interrupted cross-file updates. There is no multiwriter locking:
use one writer per workspace and do not edit a workspace during export. Trusted local
users control the workspace; hostile concurrent filesystem mutation is not supported.

The MCP server binds no network port and accepts only paths relative to its configured
root. CLI and Python API paths are explicitly controlled by the local caller.

See [architecture diagram](diagrams/architecture.md).


The stable 1.0.0 implementation includes separate environment, reproduction, experience, catalog,
Zenodo and interoperability modules. Core package management remains offline and
execution-free. Environment resolution has explicit network opt-in; builds and
analysis are offline. Public sharing is separate from local catalog publication.
Supported imports are collected in `openrepro.api`; format versions are independent
of software releases. See [launch acceptance](launch-checklist.md).
