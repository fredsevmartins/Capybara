# Troubleshooting

Start with `openrepro version --json`, the exact command's `--help`, and
`openrepro doctor PATH --json` for an existing workspace. On a supported Linux
execution host, add `--docker`. Doctor checks prerequisites; it does not run analysis.

## Installation and command discovery

| Symptom | Check and action |
| --- | --- |
| `openrepro` not found | Activate the correct venv; use `python -m pip show openrepro` and `python -m openrepro.cli version --json` to confirm interpreter selection |
| `python` not found | Try the installed `python3`/Windows `py -3` launcher when creating the venv; confirm Python 3.11–3.13 |
| PowerShell refuses activation | Call `.venv\Scripts\python.exe` and `.venv\Scripts\openrepro.exe` directly; activation is optional |
| Installer cannot download | Check the actual HTTPS/network/proxy policy and selected release URL; retain TLS verification |
| Missing dependency resolver | Install `pip>=25,<27` in this venv or use the source `environment` extra; see [installation](installation.md) |
| Version differs from expected | Check the executable's venv and install the chosen verified release in a fresh venv |

## Workspaces, packages and editing

| Symptom | Check and action |
| --- | --- |
| Destination already exists | Preserve the old output and select a new workspace/export/run path; creation never silently overwrites it |
| Checksum or inventory FAIL | Preserve evidence; restore the original bytes or make a reviewed revision with editing commands; never rewrite hashes to hide corruption |
| Reproduction WARN | Add meaningful instructions with `update --metadata`; inspect the actual issue before interpreting WARN |
| Invalid metadata | Check required fields and schema version; use [metadata editing](editing.md), not manual inventory edits |
| Input has dependents | Explicitly remove/recreate derived outputs before replacing or removing their input |
| Unsafe path/symlink | Select regular files in trusted directories; remove internal symlinks/case collisions; see portable path rules in [format](package-format.md) |
| Resource/ZIP limit | Compare actual file/count/expanded-size/ratio limits in [format](package-format.md); split an oversized research package rather than weakening import checks |
| External RO-Crate rejected | Native import accepts the generated profile; use explicit [conversion](interoperability.md) for supported local crates |
| Edit rollback failed | Stop writes and preserve the reported backup; follow [recovery](editing.md) and validate before resuming |

## Docker and reproduction

| Symptom | Check and action |
| --- | --- |
| Unsupported execution runtime | Use Linux and a trusted local daemon; macOS/Windows support is for package management, not this runner |
| Cannot access Docker socket | Ask the host administrator to configure appropriate trusted access; do not make the socket world-writable |
| Mutable/missing image | Review and load the selected image, then use its full immutable image ID; acquisition is separate from execution |
| Execution/build/download refused | Inspect the request and grant only the intended explicit `--allow-execution`, `--allow-build` or `--allow-download` flag |
| Offline dependency build fails | Confirm the lock and all compatible binary wheels are registered and hashed; unsupported platform/architecture or source-only requirements need another reviewed environment |
| Timeout, OOM or quota failure | Inspect `report.json`, retained logs and recipe limits; adjust only after reviewing the actual workload and host capacity |
| Comparison FAIL | Inspect per-output differences, units, expected paths and reference hashes; justify tolerance changes scientifically rather than increasing them just to pass |
| Interrupted run | Preserve the staging journal and use `recover` for its matching labelled container; see [execution](execution.md) |

## Catalog, Zenodo and MCP

| Symptom | Check and action |
| --- | --- |
| Catalog search empty | Confirm the catalog directory and query; `publish` writes a local catalog, not a public website |
| SQLite locked | Stop concurrent writers and retry after the active operation finishes; use one trusted writer |
| Catalog blob checksum differs | Preserve the catalog and restore a consistent backup; do not modify the index to bless altered bytes |
| No DOI after `deposit-bundle` | Expected: the bundle is local only. Review and complete [Zenodo publication](zenodo.md) |
| Zenodo 401/403 or denied destination | Check token scopes, secure binding and HTTPS policy; never paste a token into an issue or disable TLS |
| Zenodo creation/publication timeout | Preserve `zenodo.json`, inspect the actual remote record and resume the same deposition; do not delete the journal to retry |
| MCP waits silently | Stdio needs a client to initialize; it is not an interactive shell or HTTP server |
| MCP path rejected | Use paths relative to the configured trusted root, including copied sources/packages; use absolute executable/root paths in client configuration |

## Request help

Use the repository's [issues](https://github.com/fredsevmartins/Capybara/issues) for
ordinary defects or documentation problems. Include the software version, OS/Python,
exact command, sanitized output/exit code, expected behavior and a minimal synthetic
reproduction. Mention whether Docker execution was requested. Exclude tokens, private
participant data, unpublished results and identifying paths. Security issues follow
the private [disclosure policy](../SECURITY.md). See [backup and restoration](operations.md)
before attempting repairs that could affect research files.
