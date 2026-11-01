# Local RO-Crate interoperability

The native package format remains schema `0.1`; ordinary package import continues
to require the generated integrity profile. Explicit conversion accepts a broader
local RO-Crate 1.1 graph without weakening native import validation:

```bash
openrepro convert-crate external-crate --output experiments/converted --json
```

The input must contain `ro-crate-metadata.json`, context
`https://w3id.org/ro/crate/1.1/context`, a root Dataset identified by `./`, named
authors, a license and local File entities reachable through `hasPart`. Nested
Datasets are followed; cycles, duplicate/case-colliding paths, missing entities,
unsafe paths and source symlinks are rejected. URI-encoded local filenames are
decoded once and checked for portability. Remote file/context retrieval is never
performed. Use `--author` and `--license` only when the source lacks usable declarations
and you have the authority to supply them.

Declared file sizes/checksums are checked when present. Payloads have the native
128 MiB per-file and 512 MiB aggregate limits. Files not reachable through `hasPart`
are not copied. The original graph, including extra entities and fields, is archived
unmodified as `supplementary/source-ro-crate.json`; its hash and the conversion event
are recorded. Original data is preserved, and conversion writes a new destination.

Most local file paths are retained. Files colliding with required OpenRepro metadata
are placed under `supplementary/imported/`; the command returns the mapping. Conversion
creates a new experiment identity and generated profile; it does not claim semantic
JSON-LD equivalence or external RO-Crate certification. Rich original relationships
remain in the archived graph, rather than being silently inferred as scientific
provenance. Review script paths and build a new recipe before execution.

Python and POSIX-shell analyses are exercised in real Docker tests. Other languages
can use reviewed images with the same Linux runtime contract (`/bin/sh`, `sleep`,
`tar` and a selected executable); package managers for those languages are not inferred.
Use `recipe --interpreter EXECUTABLE` or an explicit argument-array recipe. This is
process-level language support, not certification of every scientific toolchain.
