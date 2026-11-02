# Supported Python API reference

Generated signatures from `openrepro.api`. Follow the [API tutorial](python-api.md)
for runnable code and error handling. All filesystem paths are `pathlib.Path`.
Use fresh destinations and a single trusted writer. Operations can raise
`OpenReproError` (a `ValueError`), validation errors or filesystem exceptions.
Functions returning a report can report FAIL without raising: inspect status.

## Comparison

`openrepro.api.Comparison`

Pydantic model; validate with `model_validate`, serialize with `model_dump(mode="json")`. See [schemas](schemas/README.md) and [package format](package-format.md).

## EnvironmentSpec

`openrepro.api.EnvironmentSpec`

Pydantic model; validate with `model_validate`, serialize with `model_dump(mode="json")`. See [schemas](schemas/README.md) and [package format](package-format.md).

## FileEntry

`openrepro.api.FileEntry`

Pydantic model; validate with `model_validate`, serialize with `model_dump(mode="json")`. See [schemas](schemas/README.md) and [package format](package-format.md).

## Manifest

`openrepro.api.Manifest`

Pydantic model; validate with `model_validate`, serialize with `model_dump(mode="json")`. See [schemas](schemas/README.md) and [package format](package-format.md).

## OpenReproError

`openrepro.api.OpenReproError`

Application error; catch before generic ValueError.

## Recipe

`openrepro.api.Recipe`

Pydantic model; validate with `model_validate`, serialize with `model_dump(mode="json")`. See [schemas](schemas/README.md) and [package format](package-format.md).

## Role

`openrepro.api.Role`

Role enumeration; see [file roles](package-format.md).

## add_file

```python
add_file(root: pathlib.Path, source: pathlib.Path, role: openrepro.models.Role, description: str = '', derived_from: list[str] | None = None) -> openrepro.models.FileEntry
```

FileEntry; copies and registers a source file, preserving the original.

## build_environment

```python
build_environment(root: pathlib.Path, spec: openrepro.environment.EnvironmentSpec, *, allow_build=False) -> dict
```

dict; image/build/cache identities. Requires allow_build=True.

## citation

```python
citation(catalog: pathlib.Path, checksum: str) -> dict
```

dict; CSL citation, content identity and DOI only when declared.

## compare_results

```python
compare_results(root: pathlib.Path, outputs: pathlib.Path, comparisons: list[openrepro.reproduction.Comparison]) -> dict
```

dict; status and per-output comparisons. No execution or Docker.

## convert_crate

```python
convert_crate(source: pathlib.Path, destination: pathlib.Path, *, license=None, authors=None) -> dict
```

dict; conversion status and destination. Preserves original metadata.

## create_experiment

```python
create_experiment(root: pathlib.Path, title: str, description: str, authors: list[str], **metadata) -> openrepro.models.Manifest
```

Manifest; creates a new workspace and required documents.

## create_recipe

```python
create_recipe(root: pathlib.Path, image: str, destination: pathlib.Path, *, script=None, reference=None, output=None, interpreter='python') -> dict
```

dict; writes a new assisted recipe. Does not execute it.

## deposit_bundle

```python
deposit_bundle(package: pathlib.Path, destination: pathlib.Path) -> dict
```

dict; local bundle identity/status; no upload or assigned DOI.

## doctor

```python
doctor(root: pathlib.Path, *, docker=False) -> dict
```

dict; status and prerequisite checks; docker=True also checks the local daemon.

## environment_plan

```python
environment_plan(root: pathlib.Path, spec: openrepro.environment.EnvironmentSpec) -> dict
```

dict; registered dependency hashes and build plan; no build.

## export_experiment

```python
export_experiment(root: pathlib.Path, output: pathlib.Path) -> pathlib.Path
```

Path; new deterministic .orepro outside the workspace.

## fetch_package

```python
fetch_package(catalog: pathlib.Path, checksum: str, destination: pathlib.Path) -> dict
```

dict; verified package import into a new destination.

## import_experiment

```python
import_experiment(package: pathlib.Path, destination: pathlib.Path) -> pathlib.Path
```

Path; newly imported, structurally validated workspace.

## inspect_experiment

```python
inspect_experiment(root: pathlib.Path) -> dict
```

dict; metadata, file inventory and validation.

## lock_environment

```python
lock_environment(root: pathlib.Path, requirements: str, base_image: str, destination: pathlib.Path, *, allow_download=False) -> dict
```

dict; registered wheels/hash lock; requires allow_download=True.

## publish_package

```python
publish_package(package: pathlib.Path, catalog: pathlib.Path) -> dict
```

dict; immutable local catalog record/revision; not Internet publication.

## recover_run

```python
recover_run(staging: pathlib.Path) -> dict
```

dict; recovery/cancellation state for the matching labelled interrupted run.

## remove_file

```python
remove_file(root: pathlib.Path, relative: str) -> None
```

None; removes a registered payload and records provenance.

## render_report

```python
render_report(run: pathlib.Path, destination: pathlib.Path) -> dict
```

dict; report path and run status; writes escaped standalone HTML.

## replace_file

```python
replace_file(root: pathlib.Path, relative: str, source: pathlib.Path) -> openrepro.models.FileEntry
```

FileEntry; revises registered bytes with rollback and provenance.

## reproduce

```python
reproduce(root: pathlib.Path, recipe: openrepro.reproduction.Recipe, destination: pathlib.Path, *, allow_execution=False) -> dict
```

dict; run status, image, logs and comparisons; explicit execution.

## reproduction_plan

```python
reproduction_plan(root: pathlib.Path, recipe: openrepro.reproduction.Recipe) -> dict
```

dict; validated recipe/input identities, without execution.

## search_catalog

```python
search_catalog(catalog: pathlib.Path, query: str = '', *, limit: int = 20, experiment: str | None = None) -> list[dict]
```

list[dict]; bounded metadata search of immutable revisions.

## update_metadata

```python
update_metadata(root: pathlib.Path, changes: dict) -> openrepro.models.Manifest
```

Manifest; updated descriptive metadata; identity/inventory preserved.

## validate_experiment

```python
validate_experiment(root: pathlib.Path) -> dict
```

dict; PASS/WARN/FAIL, issues and scientific_validity=NOT_EVALUATED.

## zenodo_deposit

```python
zenodo_deposit(bundle: pathlib.Path, *, publish=False, deposition_id: int | None = None, client=None) -> dict
```

dict; reconciled journal; publish=True explicitly requests publication.
