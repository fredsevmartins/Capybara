# Contributing to Capybara

Independent testing, documentation improvements, usability reports and research
method reviews are welcome. Capybara is the repository; its Python toolkit remains
`openrepro`. Start with the [documentation index](docs/introduction.md) and
[supported scope](docs/launch-checklist.md).

## Set up development

Use Python 3.11–3.13. Clone the repository, create/activate a venv and install
`python -m pip install -e '.[dev]'`. For the committed dependency lock, use
`uv sync --frozen --extra dev` with uv 0.12.23. See [installation](docs/installation.md).

Before submitting a focused pull request:

```bash
python -m pytest -q
ruff check .
ruff format --check .
python scripts/check_docs.py
python -m build --no-isolation
python -m twine check --strict dist/*
python scripts/check_release.py
```

Use a clean `dist` directory or name the current version's artifacts explicitly;
old files are not part of a new release. `check_docs.py` checks links/images, mirrored
diagrams, schema/reference freshness and executes the standalone CLI/API tutorials
in temporary directories. After changing CLI options or public API signatures,
regenerate with `python scripts/documentation_reference.py --write` and review the diff.

Without `OPENREPRO_TEST_IMAGE`, real Docker tests are skipped. To run them, use a
supported Linux/local Docker host, review/load `python:3.12-slim`, inspect its full
image ID, set `OPENREPRO_TEST_IMAGE` to that ID and repeat pytest. Never use a passing
portable suite as evidence that Docker tests ran. The complete reviewed download/
build/execution acceptance is documented in [verification](docs/verification.md)
and implemented by `scripts/acceptance_smoke.py` with explicit opt-in flags.

## Propose a change

Explain the concrete problem, resulting behavior, relevant limitations and actual
checks. Preserve source datasets and never weaken integrity/security checks to make
tests pass. Add regression coverage for changed behavior and document public interfaces.
Discuss breaking format changes before altering native package schema 0.1. Keep
schema/software versions distinct and preserve published release artifacts.

Use [issues](https://github.com/fredsevmartins/Capybara/issues) for ordinary defects,
feature ideas or independent test findings. Include versions, sanitized commands,
expected/actual results and a minimal synthetic example. Private vulnerabilities
follow [SECURITY.md](SECURITY.md), not public issue comments.

## Research and independent evaluation

Researchers can contribute protocols, numerical references, unit checks, model
critiques and real-world workflow feedback. Follow the [evaluation protocol](docs/pilot-protocol.md)
and record actual observations, versions, dataset attribution and unresolved findings.
Clearly distinguish synthetic examples from measurements, document methods and
justify tolerances. Review privacy, sharing rights and third-party licenses before
submitting datasets. Do not commit private participant data, credentials or fabricated
validation claims. See the [code of conduct](CODE_OF_CONDUCT.md).

## Documentation standards

Lead with a user's task and prerequisites, provide a runnable example with fresh
destinations, explain expected outcomes and link to recovery/limitations when relevant.
Keep command names and public signatures aligned with the implementation. Use UTF-8;
preserve the English technical reference and keep the Portuguese entry guide current.
Source/license attribution must accompany research examples and reused assets.
