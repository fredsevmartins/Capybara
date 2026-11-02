# CLI reference

The [complete options reference](cli-options.md) reproduces every command’s exact
help, required positional arguments, defaults and flags. All commands accept `--json`. Run `openrepro COMMAND --help` for exact argument
requirements. Source scripts never run during import, validation, planning,
comparison, recipe generation, catalog access or conversion.

| Command | Inputs and behavior |
| --- | --- |
| `init PATH` | Required title, description and repeatable author; optional license and reproduction instructions |
| `add PATH SOURCE` | Register a preserved copy with role, description and optional derived-from relationships |
| `list PATH` | List immediate experiment children |
| `inspect PATH` | Metadata, inventory and validation |
| `validate PATH` | Structural/integrity PASS, WARN or FAIL |
| `export PATH OUTPUT` | New deterministic package outside the experiment |
| `import PACKAGE DESTINATION` | Validate and import into a new directory |
| `update PATH --metadata CHANGES.json` | Validated descriptive metadata edits |
| `replace PATH FILE SOURCE` | Explicit registered payload replacement; reject inputs with dependents |
| `remove PATH FILE` | Remove a payload; protect required documents and referenced inputs |
| `version` | Installed software version |
| `plan PATH --spec RECIPE.json` | Validate recipe, references and dependency identities without execution |
| `reproduce PATH --spec RECIPE.json --output NEW_RUN --allow-execution` | Explicit offline Docker run and comparison; optional environment/allow-build |
| `compare PATH --spec RECIPE.json --outputs DIRECTORY` | Compare declared outputs without execution or Docker |
| `environment-lock PATH --requirements REGISTERED --base-image IMAGE --output NEW --allow-download` | Resolve binary Python dependencies, register exact lock/wheels |
| `environment-build PATH --spec ENVIRONMENT.json --allow-build` | Build/reuse an offline image from registered hashed inputs |
| `recipe PATH --image IMAGE --output NEW.json` | Assist script/reference selection; optional interpreter, script, reference and result-name |
| `doctor PATH --docker` | Check experiment and optional Linux/Docker capabilities without running analysis |
| `report RUN --output NEW.html` | Render an escaped standalone run report |
| `recover STAGING_DIRECTORY` | Cancel only the interrupted run's labelled container and preserve its journal |
| `publish PACKAGE --catalog DIRECTORY` | Add an immutable validated revision to a local catalog |
| `search CATALOG --query TEXT` | Search metadata; optional experiment UUID and bounded limit |
| `fetch CATALOG CHECKSUM DESTINATION` | Verify and import a catalog package into a new directory |
| `cite CATALOG CHECKSUM` | CSL JSON citation with content identity and a DOI only if declared |
| `serve CATALOG --host ADDRESS --port PORT` | Read-only HTTP discovery/download service; default local binding |
| `deposit-bundle PACKAGE --output NEW_DIRECTORY` | Prepare local Zenodo metadata/package/checksum bundle; no network |
| `zenodo-deposit BUNDLE` | Create/resume a draft; optional explicit publish or recovered deposition-id |
| `convert-crate SOURCE --output NEW_DIRECTORY` | Explicit local RO-Crate conversion; optional author/license overrides |
| `schema --kind KIND --output NEW.json` | Export manifest, recipe or environment JSON Schema |

Exit status 0 means the operation succeeded (including PASS/WARN validation).
Status 1 means a completed failed validation, comparison, reproduction, doctor check
or rendered failed report. Status 2 means invalid arguments, unsupported runtime or
an operational error. `serve` runs until interrupted. Human output is labelled;
JSON is intended for automation. Logs/results are untrusted analysis content.

Use new destinations and one trusted writer. See [editing](editing.md),
[execution](execution.md), [environments](environments.md), [exchange](exchange.md),
[Zenodo](zenodo.md) and [interoperability](interoperability.md) for complete workflows.
