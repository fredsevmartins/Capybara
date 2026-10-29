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

To manage metadata, call `load(root)`, change fields on its dumped JSON data, construct
`Manifest.model_validate(data)`, then `save(root, updated)`. Validate afterward. Never
edit checksums to conceal payload changes. Metadata updates are explicit, not automatic
scientific provenance. Errors are `OpenReproError`/`ValueError` or filesystem exceptions.
