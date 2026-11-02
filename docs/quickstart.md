# Quick start: create and exchange your first package

Install the [stable release](installation.md) and activate its venv. Work in a new
empty directory. This tutorial needs no repository checkout, Docker, credentials or
network after installation. Commands work in bash/zsh and Windows PowerShell.

## 1. Create a small protocol

Save/run this Python snippet, or create `protocol.txt` with the same text:

```python
from pathlib import Path

Path("protocol.txt").write_text(
    "Synthetic training only. Review source data and methods before analysis.\n",
    encoding="utf-8",
)
```

## 2. Create, inspect and validate

```bash
openrepro version --json
openrepro init experiments/study --title 'Model study' --description 'Synthetic training' --author 'A. Researcher' --reproduction 'Read protocol/protocol.txt; no automated analysis is supplied' --json
openrepro add experiments/study protocol.txt --role protocol --description 'Training protocol' --json
openrepro list experiments --json
openrepro inspect experiments/study --json
openrepro validate experiments/study --json
```

`init` creates the manifest, README, provenance and role directories. `add` copies
the protocol to `protocol/protocol.txt`; the source stays unchanged. Inspect the
inventory, authors and license. The default research-payload license is CC-BY-4.0;
select a license you have permission to apply using `init --license` or
[metadata editing](editing.md). The application's own license is MIT.

Validation should report `"status": "PASS"`, `"issues": []` and
`"scientific_validity": "NOT_EVALUATED"`. A WARN still exits successfully; FAIL
exits 1. An invalid command or operational error exits 2. See [CLI reference](cli-reference.md).

## 3. Export and restore a package

```bash
openrepro export experiments/study study.orepro --json
openrepro import study.orepro experiments/imported --json
openrepro validate experiments/imported --json
openrepro doctor experiments/imported --json
```

`study.orepro` is the portable ZIP package. `experiments/imported` is a separate
workspace with the same metadata and registered payload bytes. Import and doctor
do not execute analysis. Use a new destination for each import/export; preserve
existing outputs or choose another name before repeating the tutorial.

## 4. Add the package to a local catalog

```bash
openrepro publish study.orepro --catalog exchange --json
openrepro search exchange --query 'Model study' --json
openrepro deposit-bundle study.orepro --output deposit --json
```

`publish` adds an immutable catalog revision on your disk. It does not put data on
the Internet. Save the returned `sha256` if you want to fetch or cite this exact
revision; see [exchange](exchange.md). `deposit` is only a local Zenodo preparation
bundle: it has no newly assigned DOI and has not uploaded anything.

You now have the source protocol, two workspaces, a portable package, a catalog and
a local deposit bundle. Back up these research files separately from the venv.

## Next tasks

- Revise metadata or payloads: [editing and recovery](editing.md).
- Run a reviewed analysis on Linux: [execution](execution.md) and [Iris example](../examples/iris/README.md).
- Preserve a public record and DOI: [Zenodo](zenodo.md).
- Automate management: [Python API](python-api.md) or [local MCP](mcp-integration.md).
- Diagnose a failure: [troubleshooting](troubleshooting.md).
