# Installation

Capybara is the repository and product name. The installed distribution, Python
module and commands retain the name **OpenRepro**: `openrepro`, `openrepro-mcp`.
The stable release is 1.0.0. No PyPI account, API key or AI service is required.

## Requirements

| Capability | Requirements |
| --- | --- |
| Create, validate, edit, import/export, compare, local catalog | Python 3.11–3.13; Linux, macOS or Windows |
| Local MCP management | Core installation plus a compatible stdio MCP client |
| Resolve Python requirements | Linux/glibc CPython, optional `environment` extra (pip), compatible local image and explicit registry access |
| Build environments and reproduce analysis | Linux, Docker CLI and trusted local daemon at `/var/run/docker.sock`; reviewed immutable image |
| Zenodo API deposit | Reviewed public metadata/files, Zenodo account, secure token and HTTPS access |

Python newer than 3.13 is not covered by the published CI matrix. Docker Desktop
on Windows/macOS is not a supported execution host for this runner; use a Linux
machine for execution. Core package management on those systems is tested.

## Install the published release

Create a virtual environment in your working directory:

```bash
python -m venv .venv
```

Activate it with the command for your shell:

| Shell | Command |
| --- | --- |
| Linux/macOS bash or zsh | `source .venv/bin/activate` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |

On systems where Python is named `python3`, use that name when creating the venv.
If activation is unavailable, call `.venv/bin/python` or `.venv\Scripts\python.exe`
and the corresponding CLI executable directly; no system policy change is required.

```bash
python -m pip install 'https://github.com/fredsevmartins/Capybara/releases/download/v1.0.0/openrepro-1.0.0-py3-none-any.whl'
openrepro version --json
openrepro --help
```

The version result is `{"version": "1.0.0"}`. Start the
[self-contained tutorial](quickstart.md) or the [Portuguese guide](guide-pt-br.md).
Dependencies are downloaded during installation over verified HTTPS. Subsequent
local management works offline. Resolution, image acquisition and API publication
are separate operations that may require network access.

For dependency resolution in this same venv, install the supported pip range:

```bash
python -m pip install 'pip>=25,<27'
```

The `environment` extra supplies the same dependency when installing from source.
Review the [environment workflow](environments.md) before allowing downloads/builds.

## Verify a downloaded distribution

Download the wheel and `verification.json` from the **same**
[GitHub Release](https://github.com/fredsevmartins/Capybara/releases/tag/v1.0.0).
In the download directory, compare the bytes before installing:

```python
import hashlib
import json
from pathlib import Path

record = json.loads(Path("verification.json").read_text(encoding="utf-8"))
name = "openrepro-1.0.0-py3-none-any.whl"
expected = next(item["sha256"] for item in record["artifacts"] if item["file"] == name)
actual = hashlib.sha256(Path(name).read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit("Checksum mismatch: do not install")
print("SHA-256 matches the release record")
```

Then run `python -m pip install ./openrepro-1.0.0-py3-none-any.whl`.
Checksums detect changed bytes; they are not authorship signatures. Published
checksums and actual test evidence are in the [verification report](verification.md).

## Install from source or contribute

Git and a checkout are needed for repository examples and development:

```bash
git clone https://github.com/fredsevmartins/Capybara.git
cd Capybara
python -m venv .venv
# Activate the environment as above.
python -m pip install -e '.[dev]'
```

For a locked development environment, use `uv sync --frozen --extra dev` with
uv 0.12.23. A regular pip install follows compatible dependency ranges rather than
`uv.lock`. For a noneditable core installation use `python -m pip install .`;
for the resolver use `python -m pip install '.[environment]'`. Matplotlib and SciPy
are development/example dependencies, not required for core package management.

## Update or remove

Back up research workspaces and catalogs before changing software. Install a chosen
verified release into a new venv, check `version`, and validate a copied workspace
before switching normal work. Keep the old venv until the check succeeds.
[Compatibility](compatibility.md) distinguishes software and format versions.

`python -m pip uninstall openrepro` removes the application from the active venv;
it does not delete research workspaces, packages, catalogs, reports or Docker images.
Remove an unused venv only after checking that it contains no research files.
See [troubleshooting](troubleshooting.md) for installation and runtime failures.
