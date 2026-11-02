# Local operations, backup and restoration

This guide applies to the trusted, single-writer local workflow. The catalog's
built-in HTTP server is read-only and is not an authenticated multi-tenant service.
Read the [threat model](security.md) before serving research to other users.

## What to preserve

| Item | Preserve because |
| --- | --- |
| Workspace directory | Manifest, RO-Crate, README, protocols, payloads and provenance belong together |
| Exported `.orepro` files | Immutable snapshots, validated independently on import |
| Entire catalog directory | SQLite index and `packages/` blobs must remain consistent |
| Recipe/environment files and registered wheels/locks | Define reviewed commands, dependency identities, units and tolerances |
| Run directories, reports and interrupted-run journals | Record evidence and identify recoverable resources |
| Reviewed Docker image digest/archive | A mutable registry tag does not preserve a selected image |
| Zenodo bundle and `zenodo.json` | Resume the same deposition after an uncertain response |

A venv, downloaded wheel or Git checkout alone is not a research backup. Tokens
are not backup payloads; manage them separately through your secure credential system.
Workspace snapshots/backups may contain private data; apply your access/retention rules.

## Make a consistent backup

1. Stop writes, catalog publication and analysis runs. Stop the optional HTTP server
   while copying the catalog. Close clients that may be editing the same workspace.
2. Validate the workspace and preserve an exported snapshot at a new path:

   ```bash
   openrepro validate experiments/study --json
   openrepro export experiments/study backup-study.orepro --json
   ```

3. Copy complete workspace/catalog/run directories with your normal trusted backup
   tool. Preserve private file permissions and verify that the copy completed.
   Copying a live SQLite file by itself is not a consistent catalog backup.
4. Keep a second independent backup location and record the software version and
   snapshot identifiers. Test restoration before relying on the backup.

## Restore without replacing working data

```bash
openrepro import backup-study.orepro experiments/restored-study --json
openrepro validate experiments/restored-study --json
openrepro inspect experiments/restored-study --json
```

Use a new destination, compare expected metadata and registered inventory, then
review representative payloads. Test a complete copied catalog with
`openrepro search restored-catalog --query 'Study' --json`; use a returned SHA-256
with `fetch` into another new workspace and validate it. Keep the original backups
until the restored workflow is accepted. Importing and validation execute no scripts.

For a full execution restore on Linux, install the recorded reviewed image and
registered dependencies, inspect the recipe and run the explicit workflow again.
Matching regenerated outputs is useful evidence, not proof of scientific validity.

## Interrupted operations

Handled edit failures restore affected bytes; an unexpected process termination
may retain a sibling backup. Preserve it and follow [editing recovery](editing.md).
An interrupted Docker run has a staging directory and labelled container; use
`openrepro recover STAGING_DIRECTORY --json` as described in [execution](execution.md).
Do not delete backups/journals or run broad Docker cleanup as a recovery shortcut.

Zenodo timeouts can leave a real draft/publication despite a missing local response.
Preserve the bundle journal and follow [resume/reconciliation](zenodo.md), checking
the same remote record rather than creating a duplicate deposit.

## Catalog service and capacity

Bind to `127.0.0.1` unless an administrator intentionally arranges access. For
shared access use a dedicated read-only service account and a reviewed TLS/auth
reverse proxy with request/rate limits. Run publication separately with write access.
Check free disk space before copies, exports and new runs; preserve existing immutable
blobs rather than deleting them to alter revision history. There is no built-in
catalog garbage collector, backup scheduler, authentication or service manager.

## Software updates

Install the chosen verified release in a new venv. Restore a copy of a research
package, validate it and exercise the needed workflow before switching. Preserve
old software/image identities with results. See [compatibility](compatibility.md)
and the [changelog](../CHANGELOG.md) for software/schema changes.
