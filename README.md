# OpenRepro

![OpenRepro logo](docs/assets/logo.svg)

**Share Experiments. Reproduce Science.**

OpenRepro v0.1 packages scientific experiment files with a versioned manifest,
RO-Crate 1.1 metadata and SHA-256 checksums. Its CLI and local MCP server share
one offline Python core. No database, Docker, API key or AI provider is required.

Researchers need to exchange protocols, data, analysis and provenance together.
An `.orepro` file is an ordinary ZIP archive that preserves these files and checks
whether their contents still match the recorded inventory.

```mermaid
flowchart LR
    A[Researcher] --> B[CLI or local MCP]
    B --> C[OpenRepro core]
    C --> D[ZIP research package]
    D --> E[Other researcher]
```

## Installation

Python 3.11 or newer:

```bash
git clone https://github.com/fredsevmartins/OpenRepro.git
cd OpenRepro
python -m venv .venv
# Unix: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

For a locked development installation with uv, run `uv sync --frozen --extra dev`.

The project has not been published to PyPI. For core use, omit `[dev]`.

## Quick start

Run from the checkout with the environment activated. Use new destination paths:

```bash
openrepro init experiments/demo --title 'Synthetic study' --description 'Training only' --author 'Researcher'
openrepro add experiments/demo README.md --role supplementary
openrepro inspect experiments/demo --json
openrepro validate experiments/demo --json
openrepro export experiments/demo demo.orepro
openrepro import demo.orepro experiments/received
```

Validation returns `WARN` when reproduction instructions are absent, and `FAIL`
for structural or checksum errors. A passing integrity check **does not establish
scientific correctness**. Imported scripts are never executed.

## Interfaces and examples

The [CLI reference](docs/cli-reference.md) covers all commands. The
[Python API](docs/python-api.md) supports richer metadata. The
[MCP guide](docs/mcp-integration.md) explains local stdio configuration and the
current limits of ChatGPT connectivity.

```bash
python examples/generate.py --output examples/generated
openrepro validate examples/generated/pharmacokinetics --json
```

Three synthetic examples cover IV bolus pharmacokinetics, dissolution and an
independent two-group comparison. Each contains data, protocol, analysis source,
figure, calculated table and an exported package. See [expected results](docs/examples.md).

## Editing experiments

Use `openrepro update PATH --metadata changes.json` to apply descriptive metadata
changes, `openrepro replace PATH REGISTERED_FILE SOURCE` for explicit payload
replacement, and `openrepro remove PATH REGISTERED_FILE` to remove a payload.
Edits record provenance and restore affected files after handled write failures.
Dependent results must be removed before replacing their inputs. See
[editing and recovery](docs/editing.md) for examples and limits.

## Package format and integrity

Packages contain `manifest.json`, `ro-crate-metadata.json`, `README.md`,
`provenance/provenance.json`, and registered files beneath `protocol/`, `data/`,
`analysis/`, `results/` or `supplementary/`. See the [format specification](docs/package-format.md).
Exports use sorted entries and normalized timestamps and permissions. Re-exporting
an unchanged workspace is byte-identical; separately created experiments have
new identifiers and timestamps.

Imports reject unsafe paths, symlinks, case collisions, duplicate ZIP entries,
unsupported compression, inventory differences and resource-limit violations.
Checksums detect changes, but are not signatures or proof of authorship.

## Development

```bash
python -m pytest -q
ruff check .
ruff format --check .
python -m build
python scripts/check_docs.py
```

CI runs tests, lint, build and examples on Python 3.11–3.13 across Linux, macOS
and Windows. CI results must be checked on GitHub; a local Linux run does not
establish cross-platform success.

## Documentation and roadmap

Start at the [documentation index](docs/introduction.md). Mermaid diagram sources
are in [docs/diagrams](docs/diagrams).

- v0.1: workspaces, file inventory, metadata, ZIP exchange, validation, CLI, MCP,
  synthetic examples and tests.
- v0.2 (planned): sandboxed execution, dependency capture and independent comparison.
- v0.3 (planned): research exchange, persistent identifiers and discovery.
- v1.0 (planned): broader RO-Crate interoperability and multiple analysis languages.

See [contributing](CONTRIBUTING.md), [security](SECURITY.md), the [MIT license](LICENSE),
and [citation metadata](CITATION.cff). No DOI has been assigned.
