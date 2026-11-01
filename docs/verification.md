# Verification report

## v0.2.0.dev0 development checks

The new reproduction workflow was validated on Linux/Python 3.12.14 with local
Docker 28.4.0. The official Python 3.12-slim test image resolved to local ID
`sha256:ae4e8b7c575fabea88a029b6cae757f342ca2525e07f7c22272d5105c346b35e`
and repository digest
`python@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159`.

- Full suite: **126 passed**, zero skipped, 18.15 seconds, with the test image selected.
  This includes eight explicit real-Docker cases. Without
  `OPENREPRO_TEST_IMAGE`, those cases are skipped rather than counted as passed.
- Real execution verified read-only experiment inputs, non-root identity, no
  forwarded host test variable/proxy, no Docker socket and only loopback networking.
- The packaged analysis example was generated, exported, imported, executed and
  compared through the CLI. Count, mean and sample standard deviation matched.
- Nonzero exit, timeout, mismatched result, unsafe output and existing destination
  cases were exercised. Binary logs are decoded with replacement rather than crashing.
- Five capability tests verify refusal before container creation if memory, swap,
  process/CPU limits or seccomp are unavailable.
- Lint and formatting passed; the documentation checker found 65 local links,
  six mirrored Mermaid sources and fourteen CLI commands.
- Source archive and wheel built. An independently installed development wheel
  outside the checkout imported the example, executed Docker reproduction and
  compared results successfully, including image/dependency identity in its report.

The new Ubuntu Docker CI job is saved but its remote outcome has not been checked.
This report records validation before publication of the development pre-release.
Remote commit/tag publication is checked separately after the push. The stable
v0.1.1 remains separately tagged. No PyPI upload is included in these checks.
See [execution](execution.md) for limits: container isolation shares the host kernel,
output retention is not a disk quota, image distribution/dependency installation are
manual, and comparison does not establish scientific correctness.

## v0.1.1 historical baseline

Current-instance checks for the v0.1.1 editing improvements were run on Linux
with Python 3.12.14 and the committed `uv.lock`, using an isolated virtualenv.
These results describe this instance, not remote CI or a restored cloud task.

| Check | Observed result |
| --- | --- |
| `uv sync --frozen --extra dev` | Passed; repeated setup passed |
| `MPLCONFIGDIR=/tmp/openrepro-mpl .venv/bin/python -m pytest -q` | **83 passed**, no skips, 4.60 seconds |
| Real MCP stdio | Initialization, eleven tools, editing calls and invalid input rejection passed |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | 50 files formatted correctly |
| `.venv/bin/python scripts/check_docs.py` | 54 local links, six mirrored Mermaid sources and eleven CLI commands passed |
| `.venv/bin/python -m build --no-isolation` | Wheel and source archive built |
| Independent wheel installation | Installed into a separate virtualenv with normal verified registry dependencies |
| Wheel lifecycle outside checkout | Create, add, replace, update, validate, export twice, import, remove and validate passed |
| Deterministic export after editing | Two exports of the unchanged revised workspace were byte-identical |
| Provenance after round trip | Creation, addition, replacement, metadata update and removal events preserved |
| Scientific demonstrations | All three generated/exported/imported within the passing suite |
| `git diff --check` | Passed |

The MCP client requires IPC. Under restricted execution the original integration
test timed out; the full suite passed using the supported execution permission
flow, without disabling tests or assertions. Initial cache writes to the read-only
home directory were corrected by setting `UV_CACHE_DIR=/workspace/.cache/uv`.
TLS and package verification remained enabled.

The new regression suite injects failures during copying, event recording and
metadata saving, including a partial RO-Crate write. It checks that original file
bytes and valid inventory are restored for all four editing operations. A separate
test verifies recovery files are retained when rollback itself fails. Other tests
cover identity preservation, invalid metadata, protected documents, dependencies,
CLI editing, MCP editing and export/import history preservation.

The independent wheel test ran outside the checkout with Pydantic 2.14.2 and
MCP 1.30.0, exercising compatible dependency ranges as well as the locked suite.
The wheel includes the updated library and both command-line entry points.
The complete documentation and tests are included in the source archive.

`install_script` and `start_skill` are saved in the cloud environment draft.
Saving a draft does not publish the filesystem snapshot or validate a new task.
Review/save environment settings and publish through the product for future tasks.

Remote GitHub Actions outcomes, macOS/Windows behavior and Python 3.11/3.13 were
not validated in this session. The repository contains the nine-combination CI
workflow. The package version is 0.1.1. Release publication is verified separately against
the remote commit and tag after these checks. No PyPI upload or DOI registration
is included in this verification.

The supported product scope remains local package management and integrity checking.
Sandboxed execution, automatic dependency capture, independent result comparison,
public discovery and hosted ChatGPT transport are future capabilities. Scientific
validity remains `NOT_EVALUATED`. See [editing](editing.md) for recovery limits and
[security](security.md) for the single trusted writer requirement.
