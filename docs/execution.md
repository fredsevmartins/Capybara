# Reviewed analysis execution

Execution is an explicit CLI/Python workflow. It is never triggered by package
import or an MCP management tool. The native package schema remains 0.1.

## Requirements and complete example

Use Linux, the Docker CLI and a trusted local daemon at `/var/run/docker.sock`.
Host/context/TLS selectors cannot redirect the runner to a remote daemon. The
daemon must support memory/swap, CPU/process limits and default seccomp. Missing
capabilities cause refusal; no host-execution fallback is provided. Images must
already be local and identified by a complete immutable SHA-256 image ID.

Images need `/bin/sh`, `sleep`, `tar` and the selected analysis executable. Python
and shell are covered by real tests; other reviewed language images can implement
this runtime contract. Image healthchecks/entrypoints are overridden. Preparing
images or downloading dependencies is separate from offline analysis.

```bash
docker --host=unix:///var/run/docker.sock pull python:3.12-slim
REPRO_IMAGE_ID=$(docker --host=unix:///var/run/docker.sock image inspect --format '{{.Id}}' python:3.12-slim)
python examples/reproduction/generate.py --output experiments/demo --image "$REPRO_IMAGE_ID"
openrepro plan experiments/demo/experiment --spec experiments/demo/recipe.json --json
openrepro reproduce experiments/demo/experiment --spec experiments/demo/recipe.json --output runs/demo --allow-execution --json
openrepro compare experiments/demo/experiment --spec experiments/demo/recipe.json --outputs runs/demo/outputs --json
openrepro report runs/demo --output runs/demo.html
```

Use new destinations; parent directories may be created as documented by each
command. Review the actual image, scripts, command, references and tolerances.
Pulling the example tag selects the current image, after which the recipe fixes
its immutable ID. Record/preserve a registry digest or image archive for transport.
See [environments](environments.md) for automatic binary resolution and offline build.

## Recipes

Recipe schema `0.2` contains `image`, an argument-array `command`, one or more
`comparisons`, optional registered `dependency_files`, timeout, memory, CPU and
output quota. `plan` validates these inputs without executing. Unknown fields,
mutable tags, unsafe paths, duplicate output names and invalid limits fail.
There is no implicit shell expansion; selecting a shell explicitly still requires
code review and execution opt-in. A generated recipe is assistance, not approval.

A comparison declares a registered `reference`, relative `output` and mode:

- `exact`: compare file bytes through SHA-256.
- `json-numeric`: compare nested JSON structures with numeric tolerances; other
  values and object keys/array order must match. A missing tolerance justification
  is recorded as a warning.
- `quantities`: require declared units and a tolerance justification. `units` maps
  JSON pointers (for example `/sepal_length_mean`) to expected unit names. Each
  quantity must contain a numeric `value` and the exact expected `unit`. No implicit
  unit conversion occurs.

Numbers match when `abs(actual-expected) <= max(relative_tolerance *
max(abs(actual), abs(expected)), absolute_tolerance)`. Defaults are 1e-6 relative
and 1e-9 absolute. Booleans are not numbers. Invalid/duplicate-key/nonfinite JSON,
missing/unsafe outputs and files over 16 MiB fail comparison. Reports identify
up to 100 differing JSON pointers with bounded value previews and retain hashes.
No output or comparison string is evaluated as code. See [Iris](../examples/iris/README.md)
for justified tolerances and quantity units on attributed real measurements.

## Isolation and quotas

The container has no network, a read-only root filesystem, no capabilities,
`no-new-privileges`, default seccomp and a non-root identity. The validated input
snapshot is mounted read-only at `/experiment`. **There are no writable host
mounts.** Output is a dedicated `/output` tmpfs with a real filesystem quota.
`/tmp` is another 64 MiB tmpfs. Both mounts are `noexec,nosuid` with bounded inodes.
Host application credentials/variables are not forwarded and Docker proxy variables
are cleared. Reviewed image-baked variables remain the image owner's responsibility.

Defaults: one CPU, 256 MiB memory without extra swap, 64 processes, 60 seconds,
64 MiB output and a 16 MiB per-file limit. Recipe bounds allow 0.1–4 CPUs,
32–4096 MiB memory, 1–3600 seconds and 1–512 MiB output. Tmpfs uses container
memory; a workload can reach its memory limit before filling the output quota.
Analysis logs are redirected into bounded container files and retained up to the
first MiB per stream, with invalid UTF-8 replaced. Excessive logging can itself
cause a failed analysis under the file limit.

The host collects bounded tar streams only from selected container paths, validates
all archive paths/types/counts/sizes and writes fresh files. Symlinks, hardlinks,
special files, unsafe paths and more than 1000 entries are rejected. A timeout
bounds collection as well as analysis. Residual background processes are unsupported;
analysis must finish writing before it exits. Collection never trusts archive file
permissions or follows output links. Containers share the host kernel, not a VM;
use a separate VM for hostile workloads and retain external backups.

## Recovery and reports

The new external run directory contains `report.json`, `journal.json`, `stdout.txt`,
`stderr.txt` and `outputs/`. It must be outside the experiment and cannot contain
commas, which conflict with Docker bind syntax. Original files/provenance/exports
are preserved. Reports include input/recipe hashes, image/platform/digests, runtime
capabilities, dependencies, quota, timestamps, exit code, timeout and comparison.
`report` creates a self-contained HTML summary with escaped analysis content.

A private staging directory `.openrepro-run-*` holds an atomic journal before
container creation. Containers carry the exact run ID as a Docker label. If the
runner is abruptly killed, or cleanup fails, preserve this directory and run:

```bash
openrepro recover PARENT/.openrepro-run-ID --json
```

Recovery removes only the exact name/label match, marks cancellation and preserves
staging for inspection. It is idempotent. It never removes unrelated containers.
Handled successful/failed runs normally remove their containers/anonymous volumes
and staging snapshots. Infrastructure failure or unsafe output produces an error;
a completed output directory is not promised for those failures. Use one trusted
local writer and parent-directory ownership; malicious local concurrent writers
are outside the security model.

A completed run reports FAIL for timeout, nonzero exit or mismatched outputs.
PASS means only that the command exited successfully and declared outputs matched.
The script can see reference files and could copy them; this is not proof of
independent regeneration or scientific correctness. Scientific validity remains
`NOT_EVALUATED`. Independent scientific and deployment review remain release gates.

## Tests

Set `OPENREPRO_TEST_IMAGE` to a reviewed local Python image ID to run real Docker
cases; otherwise they skip. Tests exercise quotas, read-only inputs, missing host
variables/socket, network isolation, errors/timeouts, recovery, Python/shell,
offline image build and both synthetic and real-data analyses. See the
[verification report](verification.md) for actual counts and observed outcomes.
