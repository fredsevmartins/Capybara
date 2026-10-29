# v0.1 verification report

Current-instance validation: Linux, Python 3.12.14, isolated virtualenv with
`include-system-site-packages = false`. Locked versions include Pydantic 2.14.1,
MCP SDK 1.30.0, pytest 9.2.0, Ruff 0.17.3, Matplotlib 3.11.2 and SciPy 1.18.1.

| Gate | Observed result |
| --- | --- |
| `uv sync --frozen --extra dev` | Passed; repeated setup also passed |
| `.venv/bin/python -m pytest -q` | **59 passed**, zero skipped, 4.46 seconds |
| Security subset | **30 tests** included in the passing suite |
| Real MCP stdio | SDK initialization, eight tools, all calls, invalid role/path rejection passed |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | Passed |
| `.venv/bin/python -m build --no-isolation` | Wheel and source archive built |
| Independent wheel install | Installed in another virtualenv; create/register/export/import/validate passed outside checkout |
| Three synthetic demonstrations | Generated, exported and re-imported; all validate PASS |
| `.venv/bin/python scripts/check_docs.py` | 44 local links, six mirrored Mermaid sources, eight CLI commands checked |
| Mermaid rendering | All six `.mmd` files rendered to SVG using Mermaid and Chromium |
| Workflow definition | YAML parsed; read-only contents permission and nine OS/Python combinations verified |

The suite covers metadata, checksums, deterministic archive bytes, Unicode and
IRI encoding, copy preservation, CLI exit statuses, MCP structured results,
unsafe paths, symlinks, duplicate/case-colliding ZIP entries, resource limits,
malformed archives, corrupt/missing payloads, unsupported schemas and invalid JSON.
Scientific tests compare the PK model against analytical references and the Welch
interval against SciPy's independent implementation. See `tests/` for exact assertions.

The source metadata profile was checked against the official RO-Crate 1.1
specification; there is no claim of external certification or general RO-Crate support.
Validation never evaluates scientific validity. Generated numerical results are in
[example-results.json](example-results.json); portable demonstrations are in
[examples/packages](../examples/packages).

The execution sandbox blocked IPC used by the SDK client. The suite passed using
the supported execution permission flow without changing or skipping tests. An
initial package-cache-only wheel installation lacked cached dependencies; normal
verified registry installation then succeeded. TLS and artifact verification stayed enabled.

`install_script` and `start_skill` were saved in the environment configuration draft.
The draft adds `api.github.com`, needed for GitHub API visibility and Actions checks.
Saving does not apply network changes, publish the environment or validate a restored task.
The user must review/save settings and publish the prepared cloud environment.

Git read access and a push dry run succeeded. At report creation, GitHub API requests
were denied by the current network policy, and the direct repository web page returned
404. Therefore public visibility, GitHub README rendering and Actions outcomes remain
unverified. A passing local matrix does not substitute for remote CI; only Linux
Python 3.12 was executed locally. See the final delivery message for actual commit
and push outcome. No PyPI release was attempted.

Known limits: single trusted local writer, unsigned metadata, no imported code execution,
no sandboxed reproduction, strict generated RO-Crate profile, fixed archive limits,
no verified hosted ChatGPT integration. Execution/comparison (v0.2), exchange/discovery
(v0.3) and expanded interoperability (v1.0) are planned, not implemented.
