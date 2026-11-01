# CLI reference

All paths are explicit. Each command accepts `--json` after its command name.
Use `openrepro COMMAND --help` for the argument parser's authoritative options.

| Command | Inputs and behavior |
| --- | --- |
| `init PATH` | Required `--title`, `--description`, repeatable `--author`; optional `--license`, `--reproduction` |
| `add PATH SOURCE` | Required `--role`; optional `--description`, repeatable `--derived-from` registered path |
| `update PATH --metadata CHANGES.json` | Apply an object of descriptive metadata changes; preserve identity and inventory |
| `replace PATH FILE SOURCE` | Explicitly replace a registered payload; refuse inputs with dependents |
| `remove PATH FILE` | Remove a registered payload; refuse required documents and files with dependents |
| `list PATH` | List immediate experiment children in a directory |
| `inspect PATH` | Metadata, full file inventory and validation report |
| `validate PATH` | PASS, WARN or FAIL and structured issues |
| `export PATH OUTPUT` | Validate and create a new deterministic `.orepro` ZIP |
| `import PACKAGE DESTINATION` | Stage, validate and import to a new directory |
| `plan PATH --spec RECIPE.json` | Validate recipe, references and dependency files without execution |
| `reproduce PATH --spec RECIPE.json --output NEW_RUN --allow-execution` | Explicit Linux/Docker execution and comparison |
| `compare PATH --spec RECIPE.json --outputs DIRECTORY` | Compare existing outputs without Docker or execution |
| `version` | Installed software version |

```bash
openrepro add experiments/study input.csv --role raw --description 'Synthetic observations'
openrepro add experiments/study summary.csv --role table --derived-from data/raw/input.csv
openrepro validate experiments/study --json
```

Exit status: 0 for successful operations and PASS/WARN validation, 1 for FAIL
validation/comparison/reproduction, 2 for invalid arguments or failed operations. Human output uses labeled
fields; JSON uses objects suitable for tooling. CLI error messages may include caller
paths; MCP errors are sanitized to avoid disclosing machine-specific locations.

See [editing and recovery](editing.md) for complete examples, allowed metadata fields and failure handling.

For reproduction recipes, run reports and platform limits, see [execution](execution.md).
