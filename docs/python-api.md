# Python API

```python
from pathlib import Path
from openrepro.experiments import create_experiment, add_file, inspect_experiment
from openrepro.models import Role
from openrepro.packages import export_experiment, import_experiment
from openrepro.validation import validate_experiment

root = Path("experiments/api-demo")
manifest = create_experiment(
    root,
    "Synthetic study",
    "Training only",
    ["Researcher"],
    domain="pharmacokinetics",
    keywords=["synthetic"],
    institution="Example lab",
    license="CC-BY-4.0",
    reproduction="Review protocol; execute trusted scripts manually",
)
entry = add_file(root, Path("README.md"), Role.protocol, "Example protocol input")
report = validate_experiment(root)
assert report["status"] != "FAIL"
package = export_experiment(root, Path("api-demo.orepro"))
imported = import_experiment(package, Path("experiments/api-imported"))
print(inspect_experiment(imported))
```

`Manifest` and `FileEntry` are Pydantic models; use `model_dump(mode="json")`
for JSON-compatible results. `add_file` accepts `derived_from: list[str]` referencing
registered relative paths. `create_experiment` accepts `doi` and `experimental_date`
as optional metadata, in addition to the fields above. Defaults use a fresh UUID,
UTC timestamp and CC-BY-4.0 data license; choose a license you have permission to apply.

Use the transactional editing API for ordinary updates:

```python
from openrepro.experiments import update_metadata, replace_file, remove_file

update_metadata(root, {"title": "Revised study", "reproduction": "Read protocol.md"})
replace_file(root, "data/raw/observations.csv", Path("revised-observations.csv"))
remove_file(root, "results/tables/obsolete.csv")
```

Replacement and removal reject files that still have registered dependents. Remove
those derived outputs explicitly before changing their input. Required documents
cannot be removed; provenance cannot be replaced. Metadata updates preserve UUID,
creation date, schema/software versions and file inventory. See [editing](editing.md).

`load` and `save` remain low-level primitives for format tooling. They do not append
provenance or provide multi-file rollback; prefer the editing functions for user
operations. Never edit checksums to conceal payload changes. Errors are
`OpenReproError`/`ValueError` or filesystem exceptions.

## Explicit reproduction (development)

```python
from openrepro.reproduction import Recipe, reproduction_plan, reproduce, compare_results
from openrepro.experiments import load_json

recipe = Recipe.model_validate(load_json(Path("recipe.json")))
plan = reproduction_plan(root, recipe)  # no code execution or Docker access
# After reviewing image, command, input files and tolerances:
report = reproduce(root, recipe, Path("runs/new-run"), allow_execution=True)
comparison = compare_results(root, Path("runs/new-run/outputs"), recipe.comparisons)
```

The runner requires Linux/local Docker, a preloaded immutable image ID and a new
external destination. `compare_results` needs neither Docker nor execution opt-in.
See [execution](execution.md) for the report schema, defaults and limitations.
