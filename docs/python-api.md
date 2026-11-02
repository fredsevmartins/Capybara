# Python API

Use `from openrepro import api` for the supported surface. The
[complete reference](api-reference.md) covers every exported name, exact signature
and return value. Direct module imports remain compatible. Underscore-prefixed
helpers, SQLite layout and Docker internals are not public contracts.

## Complete local example

Run this in a new empty directory with the installed venv active. It needs no
checkout, network, Docker or credentials:

```python
from pathlib import Path
from openrepro import api

source = Path("api-protocol.txt")
source.write_text("Synthetic training protocol. No analysis is executed.\n", encoding="utf-8")
root = Path("api-study")
manifest = api.create_experiment(
    root,
    "API study",
    "Synthetic training only",
    ["A. Researcher"],
    license="CC-BY-4.0",
    reproduction="Review protocol/api-protocol.txt",
)
entry = api.add_file(root, source, api.Role.protocol, "Training protocol")
api.update_metadata(root, {"keywords": ["training"], "institution": "Example lab"})
report = api.validate_experiment(root)
assert report["status"] == "PASS", report
assert report["scientific_validity"] == "NOT_EVALUATED"
package = api.export_experiment(root, Path("api-study.orepro"))
restored = api.import_experiment(package, Path("api-restored"))
assert api.validate_experiment(restored)["status"] == "PASS"
record = api.publish_package(package, Path("api-catalog"))
assert api.search_catalog(Path("api-catalog"), "API study")
print(api.citation(Path("api-catalog"), record["sha256"]))
```

`Manifest` and `FileEntry` are Pydantic models. Use `model_dump(mode="json")` for
JSON-compatible results. Most other operations return dictionaries; search returns
a list, imports/exports return a `Path`, and removal returns `None`. Consult the
[reference](api-reference.md) before assuming a return shape.

## Metadata and paths

`create_experiment(..., **metadata)` accepts the optional descriptive fields listed
in [editing](editing.md), including domain, keywords, institution, DOI, experimental
date and reproduction instructions. Defaults include a new UUID, UTC creation time
and CC-BY-4.0 payload license. Choose a license appropriate to your actual rights.
`update_metadata` preserves UUID, creation date, versions and inventory.

`add_file(..., derived_from=["data/raw/input.csv"])` records relationships to
already registered relative POSIX paths. Paths supplied as roots/sources are local
`Path` objects; paths *inside a manifest* are portable relative strings. Replacement
and removal reject inputs that still have registered dependents. Remove/recreate
those derived outputs explicitly. See [editing and recovery](editing.md).

## Errors and report status

```python
from pathlib import Path
from openrepro import api

try:
    report = api.validate_experiment(Path("received-study"))
except (api.OpenReproError, OSError) as error:
    print(f"Operation could not complete: {error}")
else:
    if report["status"] == "FAIL":
        print("Validation completed but the workspace failed:", report["issues"])
```

Validation often returns a FAIL report for invalid input rather than raising.
Comparison, doctor and reproduction also return status-bearing reports; check them.
Pydantic validation and other invalid arguments may raise `ValueError`.
Publication/recovery errors require preserving local journals and inspecting the
remote state; do not retry by deleting evidence. Never log credentials/private data.

## Explicit reproduction and environments

Load a reviewed JSON recipe with `json.loads(Path(...).read_text())`, then
`api.Recipe.model_validate(...)`. `api.reproduction_plan(root, recipe)` validates
without execution. After reviewing code, image, inputs, expected outputs and
justified tolerances, call `api.reproduce(root, recipe, new_run_path,
allow_execution=True)`. This needs Linux and a trusted local Docker daemon.
`api.compare_results(root, output_directory, recipe.comparisons)` does not execute.
Render a completed report with `api.render_report(run_path, new_html_path)`.

`lock_environment(..., allow_download=True)` is explicit binary resolution;
`build_environment(..., allow_build=True)` builds offline from registered hashes.
The CLI additionally supports a combined environment/build/reproduce workflow;
`api.reproduce` itself does not accept an environment-build argument. See
[environments](environments.md), [execution](execution.md) and [signatures](api-reference.md).

## Sharing and integration

Catalog operations are local; `publish_package` is not Internet publication.
`deposit_bundle` prepares files only. `zenodo_deposit` reads credentials from the
secure runtime environment and publishes only with explicit `publish=True`.
Conversion, doctor and recipe helpers never execute imported analysis.
See [exchange](exchange.md), [Zenodo](zenodo.md), [conversion](interoperability.md)
and [compatibility](compatibility.md) for operational boundaries.
