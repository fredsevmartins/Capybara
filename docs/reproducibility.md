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
an installed OpenRepro package. The v0.1 release preserves instructions and files without executing them. The v0.2
development CLI adds an explicit [Docker reproduction workflow](execution.md),
recording image identity, architecture, recipe and dependency-file hashes, then
comparing declared results. It does not infer or install dependencies automatically.
The original three demonstration generators still use their manual workflow; a
separate dependency-free statistics example exercises the Docker runner.

[Reproducibility concept diagram](diagrams/reproducibility.md)
