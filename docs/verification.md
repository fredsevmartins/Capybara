# Verification report

## Rc2 reliability, branding and publication follow-up

After the cross-platform correction, local validation passed **180 tests**, zero
skipped, in 35.21 seconds. New cases verify interrupted catalog blob copies can
be removed/retried, including Windows file-handle semantics, and CI reporting keeps
passed/failed/error/skipped outcomes distinct. JUnit artifacts and escaped summaries
preserve the original pytest failure status.

The official actionlint 1.7.7 binary was downloaded and verified against its
upstream SHA-256 checksum; workflow validation passed. The tagged release workflow
now gates GitHub publication on the full compatibility matrix and verified artifacts.
PyPI remains deferred and cannot run from a tag push. Repro's transparent PNG was
checked as 1254×1254 RGBA with a transparent alpha channel and included in source
package inventory checks.

## DOI publication and cross-platform follow-up

The user supplied the published Zenodo record page for 23869679, titled OpenRepro
1.0.0rc1, with concept DOI 10.5281/zenodo.23869678. The screenshot confirms a public
record; the ZIP/tag identity is unverified because direct Zenodo access returns 403.
The citation uses the project/concept DOI, without assigning the rc1 version DOI to rc2.

The public GitHub Actions page is now readable even though API access is denied.
[Run 41354516427](https://github.com/fredsevmartins/OpenRepro/actions/runs/41354516427)
for commit 132b9b1 showed Linux and reproduction success, but all macOS/Windows
matrix jobs failed during pytest. Detailed logs require additional access.
Local reproductions identified directory-alias rejection (macOS temporary paths)
and an incorrect fixed 8-byte fixture size under Windows CRLF. Rc2 canonicalizes
explicit selection roots while retaining internal symlink rejection and uses actual
fixture sizes. Regressions exercise aliases, LF/CRLF preservation and invalid sizes.
The rc2 local full suite passed **177 tests**, zero skipped, in 35.16 seconds,
including all 14 Docker cases and the new path/newline regressions. Lint, schema/docs,
build and strict Twine checks passed. The corrected remote matrix is checked
separately after pushing these changes.

[Run 41357838154](https://github.com/fredsevmartins/OpenRepro/actions/runs/41357838154)
for commit 7417492 completed successfully. Its nine OS/Python matrix combinations
and the reproduction job passed. This closes the previously observed macOS/Windows
failures for that commit; subsequent changes receive their own checks.


## 1.0.0rc1 candidate

Current-instance validation: Linux x86_64, Python 3.12.14, local Docker 28.4.0.
The committed development lock and independently installed compatible dependencies
were exercised. No external participant or scientific approval is claimed.

| Check | Observed result |
| --- | --- |
| Full suite with reviewed Docker image | **170 passed**, zero skipped, 30.96 seconds |
| Final RO-Crate malformed-input hardening | Nine targeted cases passed, including three additional cases after the full-suite run |
| Real Docker subset | 14 cases included: isolation, failures, quota, recovery, offline build, Python/shell and Iris |
| Incorrect hash against an already installed dependency | Rejected; forced reinstall preserves hash verification |
| Final offline-build/cleanup regression | Passed separately after adding forced intermediate cleanup |
| Binary dependency resolution | Actual PyPI download of six 1.17.0; exact hashes registered; offline image imported the expected version |
| Locked setup | `uv sync --frozen --extra dev` passed |
| Lint/format | Passed; all Python files formatted |
| Documentation | Local links, six mirrored Mermaid sources and all 29 CLI commands checked |
| Wheel/source build | Both candidate distributions built |
| Twine | Both candidate artifacts passed strict metadata/readme checks |
| Distribution inventory | Version, required modules/docs/data and wheel-source bytes checked |
| Independent wheel install | Complete CLI workflow passed from site-packages outside editable source |
| Independent source install | API, export/import, catalog and validation passed in another fresh virtualenv |
| Zenodo integration | Offline protocol tests passed, including retries, unknown creation, checksum mismatch, foreign links and publication reconciliation |
| Public PyPI name lookup | HTTP 404 observed; name ownership/trusted publishing remains unverified |

The independent wheel acceptance resolved and registered a dependency, built its
image offline, ran the attributed Iris analysis, checked eight quantities and exact
sample count, rendered HTML, exported/published/searched/fetched/cited a package,
prepared a local Zenodo bundle, exported schemas and converted an external RO-Crate.
Its installed module path was in a separate virtualenv. The accepted package's
identity is recorded in the local acceptance artifacts, not invented as a DOI.

A real runner process was killed abruptly; its saved run ID/label allowed explicit,
idempotent recovery without deleting unrelated containers. Real output exhaustion
returned ENOSPC at the configured tmpfs quota. Source dataset bytes are pinned and
preserved across checkout platforms through `.gitattributes`.

The local acceptance scripts do not create a public deposit. The actual inspected
cloud runtime had no Zenodo or PyPI token; external trusted-publisher configuration
was not verified.
Configuration requirements were saved, but a saved draft is not an injected value
or an applied network policy. Live Zenodo/DOI publication, PyPI distribution,
remote OS/Python CI outcomes and independent-user/scientific/security acceptance
remain outstanding. See the [launch checklist](launch-checklist.md) and
[independent pilot protocol](pilot-protocol.md).

The candidate tag/publication is verified separately after the Git push. This report
records checks before publication and does not claim a GitHub Release page, PyPI
upload, DOI or restored-task validation. Stable 1.0 acceptance remains blocked by
the concrete external gates; the candidate is labelled accordingly.

## Historical checks

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
