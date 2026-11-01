# OpenRepro

<p align="center">
  <img src="docs/assets/repro-mascot.png" width="280" alt="Repro, the capybara scientist holding a verified research package">
</p>

Meet **Repro**, our capybara scientist and companion for reproducible research.
[Brand assets and usage](docs/branding.md).

**Share Experiments. Reproduce Science.**

[Project DOI: 10.5281/zenodo.23869678](https://doi.org/10.5281/zenodo.23869678).
The manually published record titled 1.0.0rc1 is
[10.5281/zenodo.23869679](https://doi.org/10.5281/zenodo.23869679).
The uploaded ZIP is named `OpenRepro-main.zip`; its exact correspondence with the
rc1 tag has not yet been independently checked. The rc2 corrections are a later
revision and do not replace files in that deposit.

OpenRepro packages protocols, data, analysis and provenance into portable `.orepro`
archives. It validates integrity, runs explicitly reviewed analysis in Linux Docker,
compares outputs, and exchanges immutable package revisions through a searchable
catalog or Zenodo.

This checkout is **1.0.0rc2, a release candidate**. Local engineering checks do not
establish independent scientific validation, public deployment or a published DOI.
See the [launch checklist](docs/launch-checklist.md) for the remaining release gates.

## Install

Python 3.11+; package management works on Linux, macOS and Windows:

```bash
python -m venv .venv
# Unix: source .venv/bin/activate
# Windows: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

For the locked development environment, use `uv sync --frozen --extra dev`.
`.[environment]` installs the optional Python dependency resolver. Core package
management needs no database service, API key, Docker or AI provider. Execution
and environment construction require Linux and a trusted local Docker daemon.
Distribution currently uses GitHub and Zenodo. PyPI publication is optional and
has been deferred; use this checkout for installation.

## Create and exchange a package

Use new destination paths:

```bash
openrepro init experiments/study --title 'Study' --description 'Research description' --author 'Researcher' --reproduction 'Review protocol and analysis'
openrepro add experiments/study observations.csv --role raw
openrepro inspect experiments/study --json
openrepro validate experiments/study --json
openrepro export experiments/study study.orepro
openrepro import study.orepro experiments/received
```

`validate` reports PASS, WARN or FAIL. Integrity does not establish authenticity or
scientific correctness. Importing, planning, catalog search and MCP management never
execute imported scripts. Explicit execution uses a separate reviewed workflow.

## Reproduce analysis

The dependency-free demonstration packages a real analysis script and synthetic CSV:

```bash
docker --host=unix:///var/run/docker.sock pull python:3.12-slim
REPRO_IMAGE_ID=$(docker --host=unix:///var/run/docker.sock image inspect --format '{{.Id}}' python:3.12-slim)
python examples/reproduction/generate.py --output experiments/demo --image "$REPRO_IMAGE_ID"
openrepro plan experiments/demo/experiment --spec experiments/demo/recipe.json --json
openrepro reproduce experiments/demo/experiment --spec experiments/demo/recipe.json --output experiments/demo-run --allow-execution --json
openrepro report experiments/demo-run --output experiments/demo-report.html
```

Execution uses immutable image IDs, no network, read-only inputs, a non-root user,
CPU/memory/process limits and a real tmpfs output quota. No writable host directory
is mounted. Reports retain image and dependency identities, exit status, numerical
comparisons and tolerance justifications. Containers share the host kernel; use a
separate VM for hostile workloads. See [execution](docs/execution.md).

[Environment preparation](docs/environments.md) resolves binary dependencies,
registers an exact SHA-256 lock and builds offline. `recipe` helps select scripts
and references; `doctor` checks prerequisites; `recover` cancels interrupted runs.
The [Iris example](examples/iris/README.md) reproduces descriptive statistics from
attributed historical observations, with units and independent NumPy references.

## Publish and discover research

```bash
openrepro publish study.orepro --catalog exchange
openrepro search exchange --query 'Study' --json
# Use the returned SHA-256 for fetch and cite:
openrepro fetch exchange PACKAGE_SHA256 experiments/retrieved
openrepro cite exchange PACKAGE_SHA256 --json
openrepro deposit-bundle study.orepro --output deposit
```

The catalog keeps immutable package bytes, revision histories and content identifiers.
An optional read-only HTTP service supports discovery and verified downloads.
Zenodo integration creates resumable drafts and publishes only with explicit
`--publish`; credentials belong in secure environment settings. A local content URN
is not a DOI. See [exchange](docs/exchange.md) and [Zenodo](docs/zenodo.md).

## Edit and integrate

`update`, `replace` and `remove` preserve identity, record provenance and restore
affected files after handled failures. Dependent outputs must be removed before
revising their inputs. See [editing and recovery](docs/editing.md).

The [Python API](docs/python-api.md) exposes supported functions through
`openrepro.api`; the local [MCP server](docs/mcp-integration.md) provides eleven
management tools without execution. Explicit [RO-Crate conversion](docs/interoperability.md)
accepts local files, preserves the original graph and never resolves remote contexts.
Published [JSON schemas](docs/schemas/README.md) describe format versions separately
from the software version.

## Development and release

```bash
python -m pytest -q
ruff check .
ruff format --check .
python scripts/check_docs.py
python -m build --no-isolation
python -m twine check --strict dist/*
python scripts/check_release.py
```

Docker tests require `OPENREPRO_TEST_IMAGE` set to a reviewed local Python image ID;
without it they are skipped. CI defines nine portable OS/Python combinations and
a separate real-Docker job. Remote CI results must be checked independently.
The [GitHub release workflow](docs/github-releases.md) verifies tagged artifacts
before attaching them to a Release. PyPI publication remains optional and deferred. See [verification](docs/verification.md), [compatibility](docs/compatibility.md)
and the [documentation index](docs/introduction.md).

MIT-licensed software. Research payloads retain their declared licenses. See
[contributing](CONTRIBUTING.md), [security](SECURITY.md) and [citation metadata](CITATION.cff).
