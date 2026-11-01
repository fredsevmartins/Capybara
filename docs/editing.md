# Editing and recovery

OpenRepro supports a local, single-writer experiment lifecycle. Imports never execute scripts. Reviewed code can run only through the separate
opt-in [reproduction workflow](execution.md). Exported packages are immutable outputs: editing a workspace
requires a new export to share the revision.

## Metadata updates

Create `changes.json` containing the fields to change:

```json
{
  "title": "Revised study",
  "authors": ["Researcher"],
  "reproduction": "Review protocol/protocol.md and run trusted analysis manually"
}
```

```bash
openrepro update experiments/study --metadata changes.json --json
```

Allowed fields: `title`, `description`, `authors`, `license`, `domain`, `keywords`,
`doi`, `institution`, `experimental_date` and `reproduction`. Values use the manifest
schema; experimental dates use ISO `YYYY-MM-DD`. Optional nullable fields can be
cleared with JSON `null`. Lists replace the whole list. Empty updates, unknown
fields and invalid values fail without changing the workspace. Identity, creation
date and inventory cannot be modified through this operation. Updating title or
description does not rewrite your README; revise that document explicitly if needed.

## Payload revisions

```bash
openrepro replace experiments/study data/raw/input.csv revised-input.csv --json
openrepro remove experiments/study results/tables/obsolete.csv --json
openrepro validate experiments/study --json
openrepro export experiments/study revised-study.orepro --json
```

The registered path, role, description and upstream relationships are retained on
replacement; only bytes, size and checksum change. The replacement must be a separate
regular file. Original source files are preserved. Missing registrations, unsafe
paths and source symlinks are rejected. README may be explicitly replaced, but
neither README nor provenance may be removed. Provenance cannot be replaced.

If another registered file declares `derived_from` pointing to the target, removal
and replacement fail. Explicitly remove dependent outputs starting with downstream
leaves, replace the input, then regenerate and register results. This prevents old
outputs from silently retaining links to revised input bytes. Undeclared scientific
dependencies cannot be detected automatically.

## Provenance

Successful add, replace, remove and metadata update operations append a UTC event.
Replacement records old and new SHA-256 values; removal records the removed hash;
metadata updates record field names. The provenance file's own inventory checksum
and generated RO-Crate metadata are updated together. Failed edits do not append
successful-operation events. Packages created before this feature still work.
This is an unsigned descriptive history, not proof of authorship or scientific validity.

## Failure handling

Edits require a valid workspace (`PASS` or `WARN`) before starting. A temporary
sibling directory `.openrepro-backup-*` stores metadata, provenance and affected
existing payloads. Copies are completed before mutation. The operation validates
the resulting workspace and restores the original affected bytes on handled errors,
including partial copies and interrupted metadata writes. Temporary empty role
directories may remain; they do not affect validation or exported bytes.

The parent directory must be writable and have space for backups. Use one trusted
writer and keep external backups. There is no lock, database transaction or guarantee
against process termination, power loss, filesystem loss or concurrent modification.
Readers should wait until editing finishes.

If restoration itself fails, the error identifies a retained backup directory.
Stop editing, fix storage permissions/capacity and preserve that directory. Its
`recovery.json` records the absolute workspace, ordered `paths` and `originals`.
For each numeric backup file `N` still present, restore it to workspace path
`paths[N]`; missing numeric files may already have been restored. Paths absent from
`originals` were created by the failed edit and should be removed. Preserve a copy
before manual recovery and run `openrepro validate` before resuming work. An orphan
backup after process termination requires inspection: the edit may already have
completed, so do not blindly restore it.


Parent directory aliases in explicitly selected local paths are canonicalized,
including macOS temporary-directory aliases. Direct source/workspace symlinks and
symlinks inside the experiment remain rejected. Newline bytes are preserved;
metadata sizes/checksums must describe actual bytes on each platform.
