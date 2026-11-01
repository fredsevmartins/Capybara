# Installation

Requires Python 3.11+. From the repository root:

```bash
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Unix or
`.venv\Scripts\Activate.ps1` in Windows PowerShell, then:

```bash
python -m pip install -e '.[dev]'
openrepro version
```

Core dependencies are Pydantic 2 and the official MCP SDK 1.x. The SDK is bounded
below 2 because its FastMCP API is used directly. Matplotlib and SciPy are example
and development dependencies. The CLI uses argparse from the standard library.

No network access is required after dependencies are installed. No service or
credential is needed for local CLI/MCP functionality. Package registry downloads
use normal TLS verification. An editable install links source changes immediately.
For a noneditable install, run `python -m pip install .`.


The candidate's optional `environment` extra supplies pip for binary requirement
resolution; `dev` includes it plus distribution checks. Execution/build requires
Linux, local Docker with enforced limits, and reviewed immutable images containing
`/bin/sh`, `sleep` and `tar`. Package management, comparison and catalogs do not need
Docker. See [environment setup](environments.md) and [release acceptance](launch-checklist.md).
