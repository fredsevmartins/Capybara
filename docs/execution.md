# Opt-in reproduction (v0.2 development)

This workflow executes reviewed analysis in a local Linux Docker container and
compares declared output files with registered references. Import, validation,
inspection, planning and comparison never execute analysis code. Execution is not
exposed through MCP. Package schema 0.1 and existing `.orepro` files are unchanged.

## Prerequisites and complete example

Use Linux with a trusted local Docker daemon at `/var/run/docker.sock`, Docker CLI
on PATH and access to its socket. The runner explicitly uses that local socket,
ignoring Docker host/context/TLS selectors. Remote daemons and Docker Desktop on
macOS/Windows are not supported by this first implementation. Package management,
planning and comparison remain cross-platform.

The daemon must support memory/swap, CPU and PID limits and default seccomp.
Missing prerequisites cause an error; there is no host-process execution fallback.
Prepare and review the image separately. The runner never pulls or builds images.
In managed cloud environments preserve the configured proxy, CA trust and registry
authentication when pulling/building; never disable TLS verification.

From an activated OpenRepro development checkout:

```bash
docker --host=unix:///var/run/docker.sock pull python:3.12-slim
REPRO_IMAGE_ID=$(docker --host=unix:///var/run/docker.sock image inspect --format '{{.Id}}' python:3.12-slim)
python examples/reproduction/generate.py --output experiments/repro-demo --image "$REPRO_IMAGE_ID"
openrepro import experiments/repro-demo/experiment.orepro experiments/repro-received
openrepro plan experiments/repro-received --spec experiments/repro-demo/recipe.json --json
openrepro reproduce experiments/repro-received --spec experiments/repro-demo/recipe.json --output experiments/repro-run --allow-execution --json
openrepro compare experiments/repro-received --spec experiments/repro-demo/recipe.json --outputs experiments/repro-run/outputs --json
```

Use new destination names. The example contains four synthetic observations, a
registered standard-library Python script, a dependency declaration and reference
statistics. It computes count=4, mean=2.5 and sample SD≈1.2909944487358056 from the
packaged CSV. It does not require scientific Python packages in the image.

Review image origin, script, command arguments, references and tolerances before
passing `--allow-execution`. Pulling a tag in this example selects a current image;
the generated recipe records the resolved immutable ID, not the mutable tag. The
report also records repository digests when the image has them. On another machine
pull the reviewed repository digest or load a verified image archive, confirm its
ID, then use the recipe. An ID alone does not distribute an image.

## Recipe schema

Recipes are separate JSON documents, schema `0.2`. `image` must be a complete local
`sha256:` image ID (64 lowercase hex digits). A representative recipe is:

```json
{
  "schema_version": "0.2",
  "image": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "command": ["python", "analysis/scripts/analyze.py"],
  "dependency_files": ["supplementary/requirements.txt"],
  "timeout_seconds": 60,
  "memory_mb": 256,
  "cpus": 1,
  "comparisons": [
    {
      "reference": "results/tables/summary.json",
      "output": "summary.json",
      "mode": "json-numeric",
      "relative_tolerance": 0.000001,
      "absolute_tolerance": 0.000000001
    }
  ]
}
```

Replace the zero placeholder with a reviewed local image ID. Unknown fields,
unsafe paths, mutable image tags, empty commands/comparisons, duplicate output
names and invalid resource limits are rejected. Commands are argument arrays;
there is no implicit shell expansion. An explicitly requested shell is still code
execution and requires review. The image entrypoint and healthcheck are overridden.

All references and dependency files must be registered. Dependency recording means
recording the selected inventory paths and hashes alongside the image identity;
it does not discover missing imports, run `pip freeze`, resolve dependencies or
install them. Prepare all required software in the image before execution.

## Container and resource policy

The container runs with no network, a read-only root filesystem, all capabilities
dropped, `no-new-privileges`, default seccomp and a non-root UID/GID. It receives a
validated snapshot of the experiment at `/experiment` (working directory, read-only)
and a dedicated writable output directory at `/output`. `/tmp` is a 64 MiB tmpfs
with `noexec,nosuid`. No Docker socket or host home directory is mounted. Host
application variables are not forwarded; Docker proxy variables are explicitly
cleared. Environment variables baked into the reviewed image remain its responsibility.

Defaults: one CPU, 256 MiB memory with no extra swap, 64 processes, 60 seconds,
16 MiB maximum file writes and bounded Docker log rotation. Recipes allow 0.1–4
CPUs, 32–4096 MiB memory and 1–3600 seconds. The runner kills timed-out containers
and removes its containers and anonymous volumes in cleanup. Logs retain at most
the last 200 lines and one MiB per stream; they may be truncated.

Outputs are checked before retention: at most 1000 directory/file entries, 64 MiB
total and only regular files/directories. Symlinks and special files are rejected.
The retention limit is checked after execution, not a filesystem quota: a process
can temporarily consume more output disk space by creating many files. Use a
quota-controlled execution disk or separate VM for hostile workloads. Docker shares
the host kernel and is not a VM or a security certification. Abrupt termination or
daemon failure can require manual cleanup of a reported `openrepro-*` container;
never remove unrelated containers.

## Reports and comparison

A new external run directory contains `report.json`, `stdout.txt`, `stderr.txt`
and `outputs/`. It must be outside the experiment and cannot contain commas (Docker
mount syntax). The input snapshot is removed. Original files, provenance and old
exports are unchanged. The report records experiment UUID, manifest hash, recipe,
normalized recipe hash, image ID/platform/repository digests, Docker capability/version
observations, selected dependency-file hashes, timestamps, exit code, timeout and
per-file comparison results. Logs/output bytes are untrusted analysis output.

`exact` compares bytes using SHA-256. `json-numeric` compares nested JSON objects
and arrays: object keys and array lengths/order must match; numeric values use
`abs(actual-expected) <= max(relative_tolerance * max(abs(actual), abs(expected)),
absolute_tolerance)`. Strings, nulls and booleans must match exactly; booleans are
not numbers. Duplicate keys, nonfinite values, invalid JSON, missing/unsafe files
and files over 16 MiB fail comparison. No output is evaluated as code.

Exit status 0 means successful operation/comparison, 1 means a completed failed run
or comparison, and 2 means invalid input, missing opt-in, unsupported runtime or
infrastructure error. Timeouts and nonzero analysis exits produce failed reports
when Docker remains available. Infrastructure errors and rejected unsafe outputs
raise errors and do not retain a completed run directory. Existing destinations are
preserved. Use one trusted local writer; concurrent local modifications are unsupported.

PASS means the command exited successfully and selected files matched under the
chosen tolerances. It does not prove scientific correctness or independent
regeneration: a script can copy reference data visible in its experiment. Reports
always retain `scientific_validity: NOT_EVALUATED`. Review methods and dependencies
and use independent scientific validation as appropriate.

## Development validation

The portable suite exercises recipe validation and comparisons without Docker.
The real runner tests require explicit opt-in via a reviewed local Python image:

```bash
OPENREPRO_TEST_IMAGE="$REPRO_IMAGE_ID" python -m pytest tests/test_reproduction_docker.py -q
```

Without that variable the eight Docker cases are skipped, not counted as passed.
CI adds a dedicated Ubuntu job that pulls the official Python image, resolves its
ID and runs those tests, including packaged CSV analysis, read-only inputs,
non-root execution, absence of host variables/socket, network isolation, timeout,
nonzero exits, mismatches, unsafe outputs and destination preservation.
