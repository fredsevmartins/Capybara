# JSON schemas

- [Package manifest 0.1](manifest.schema.json)
- [Execution recipe 0.2](recipe.schema.json)
- [Environment specification 1](environment.schema.json)

These definitions are generated from the software’s typed models and reject
unknown fields. Fixed version strings are expressed as JSON Schema constants.
Portable path normalization, local filesystem checks, graph relationships and
runtime availability also require the application validator; JSON Schema alone
does not validate an experiment's scientific meaning or payload bytes.

Export the installed schema with `openrepro schema --kind manifest --output schema.json`
(or `recipe` / `environment`). Use a new output filename. Review schema changes
alongside the compatibility policy before publishing a release.
