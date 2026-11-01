# Compatibility and supported API

The software release version, package schema, recipe schema and environment schema
are independent. The stable release uses software `1.0.0`, package schema
`0.1`, recipe schema `0.2` and environment schema `1`. JSON schemas are published
under [schemas](schemas/README.md), and `openrepro schema --kind ... --output ...`
exports the currently installed definition.

`openrepro.api` is the supported convenience import surface. Existing direct imports
from `experiments`, `packages`, `models` and `validation` remain available. Public
function signatures and structured return fields are documented in the Python API.
Underscore-prefixed helpers, Docker command construction, local SQLite layout and
recovery backup implementation details are internal contracts.

Old committed `.orepro` examples are imported, validated, exported and re-imported
in regression tests without changing their metadata. Optional recipe fields extend
the existing schema; old recipes keep default resource settings and comparison
behavior. Unknown package/schema versions fail explicitly. No imported script runs
as part of migration or validation.

Format-breaking changes require a new schema version and an explicit conversion
path. Software patch releases preserve supported behavior. Stable 1.0 covers the trusted
local workflow described in the [release scope](launch-checklist.md). External
scientific, usability and security evaluations remain unperformed. Actual remote
matrix outcomes are recorded in the [verification report](verification.md).
