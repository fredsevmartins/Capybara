# Reproducibility

An unchanged workspace exports byte-identically: sorted POSIX file names, ZIP_STORED,
normalized timestamps and permissions. New experiments have fresh UUIDs and timestamps,
so independently generated packages need not be identical. Example numeric values are
deterministic in the tested Python/SciPy environment; PNG bytes can vary by library,
font and platform. The committed `uv.lock` locks the development dependencies. Use
`uv sync --frozen --extra dev` to reproduce them. Plain pip installation uses
compatible ranges instead; operating system and fonts still affect rendered figures.

`analysis/scripts/generate.py` in each example rebuilds all demonstrations when run
manually with the `dev` extra installed and a fresh `--output` directory. It requires
an installed OpenRepro package. Automated execution of arbitrary imported scripts,
sandboxing, environment capture and independent comparison are planned for v0.2.
OpenRepro v0.1 preserves instructions and files, but does not run that workflow for you.

[Reproducibility concept diagram](diagrams/reproducibility.md)
