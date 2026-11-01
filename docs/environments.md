# Rebuildable Python environments

Environment preparation has three separate steps: resolve/download reviewed registry
requirements, register exact locks and wheels, then build a local image offline.
Analysis execution remains offline and never installs dependencies implicitly.

## Automatic binary resolution

Install the `environment` extra (already present in `dev`). Start with a valid
experiment, a reviewed local CPython image ID and a requirements file containing
registry requirements such as `six==1.17.0`. Register it, then resolve:

```bash
openrepro add experiments/study requirements.in --role supplementary
openrepro environment-lock experiments/study --requirements supplementary/requirements.in --base-image "$REPRO_IMAGE_ID" --output environments/study --allow-download --json
openrepro environment-build experiments/study --spec environments/study/environment.json --allow-build --json
```

Create the `environments` parent first if needed. Resolution downloads binary wheels
only, never source distributions or editable/VCS/direct-URL requirements. It derives
manylinux compatibility from the base image's glibc and records every resolved wheel
with an exact version and SHA-256. Nested requirements, custom indexes and pip flags
inside the input file are rejected. TLS and registry artifact verification stay on;
managed cloud proxy/CA settings must be preserved.

The first resolver supports Linux/glibc CPython with the same Python minor version
and CPU architecture as the host resolver. This avoids incorrect marker evaluation
for a different interpreter. Alpine/musl, cross-architecture resolution and non-Python
package managers are not inferred. Use a separately prepared pinned image for those
workflows. Wheel compatibility and package availability still constrain resolution.

The command registers `supplementary/requirements.lock` and the wheel files in the
experiment, recording one environment-lock provenance event. Inputs are preserved;
existing registered names are not overwritten. Registration rolls back on handled
failure. The external destination contains a reusable `environment.json`, lock and
wheelhouse. It is created only after successful resolution and registration.

## Offline build and execution

The environment specification names an immutable local `base_image`, a registered
`requirements` hash lock and registered `wheels`. For standard-library-only analyses,
both requirements and wheels may be omitted. All inputs must match the inventory.

The builder generates its own Dockerfile and runs pip with `--no-index`,
`--require-hashes`, `--only-binary=:all:` and Docker networking disabled. It never
runs a user-supplied Dockerfile. Files and base image are fingerprinted; a matching
local build is reused. Returned image IDs identify immutable results. Rebuilding
locked inputs is supported, but byte-identical image layers across Docker/build
versions are not promised. A cached Docker daemon is trusted local infrastructure.

Use the returned image in a reviewed recipe, or combine build and execution:

```bash
openrepro reproduce experiments/study --spec recipe.json --environment environments/study/environment.json --allow-build --output runs/study --allow-execution --json
```

The combined workflow records the environment fingerprint and selected image in the
run report and includes all locked inputs in dependency identities. It requires both
build and execution opt-ins. Create a recipe with `openrepro recipe` if the experiment
has a single registered script and reference table; choose explicitly when ambiguous.

Image distribution is separate: push/pull a verified registry digest or transport a
verified image archive. Building does not push an image or publish research. The base
image supplies operating-system dependencies; system libraries are not discovered or
installed automatically. Offline build failures remain errors, not permission to
ignore hashes or enable analysis networking.
