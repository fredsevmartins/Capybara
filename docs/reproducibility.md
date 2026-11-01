# Reproducibility and interpretation

An unchanged workspace exports byte-identically: sorted POSIX names, stored ZIP
entries, normalized timestamps and permissions. Newly created experiments have new
UUIDs/timestamps; independently generated packages need not have identical bytes.

The committed `uv.lock` fixes the development dependencies. Use
`uv sync --frozen --extra dev`. Plain pip installation uses compatible ranges.
Operating-system libraries, CPU architecture and fonts can still affect analyses
and rendered figures. Offline environment builds use immutable base IDs and hashed
binary wheels; they are rebuildable from selected inputs, without promising identical
Docker layer bytes across build engines.

[Execution](execution.md) records image identity, recipes, input hashes and selected
dependency hashes and compares outputs. It does not infer scientific validity.
[Environment preparation](environments.md) resolves explicit Python requirements;
it does not discover every import or system dependency. Numeric comparison needs
justified tolerances and explicit units. See the [attributed Iris case](../examples/iris/README.md)
and the three original synthetic examples.

Sharing requires preserving complete data, protocols, methods, dependency identities,
licenses and provenance. A successful replay is useful evidence, but independent
researchers must assess the method, source data and expected outcomes. Source hashes
and result equality alone do not prove authorship, correctness or new findings.

[Reproducibility concept diagram](diagrams/reproducibility.md)
