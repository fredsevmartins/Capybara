# Contributing

Use Python 3.11+ and install `python -m pip install -e '.[dev]'`. Before submitting:

```bash
python -m pytest -q
ruff check .
ruff format --check .
python -m build
python scripts/check_docs.py
```

Submit focused pull requests with the problem, resulting behavior and actual checks.
Preserve source datasets and never weaken security checks to make tests pass. Add
regression tests for changed behavior and document public interfaces. Researchers can
contribute synthetic protocols, numerical references, unit checks and model critiques.
Clearly distinguish synthetic data from observations and include license/provenance.
Discuss format changes before changing schema 0.1. Do not commit private data or keys.
