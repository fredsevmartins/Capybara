# Experiment Lifecycle

Create a workspace, register protocol/data/scripts, validate and export. Share the
archive yourself; the receiver imports into a new directory. Registration copies
bytes and records checksums and provenance.

Use `update` for descriptive metadata changes. To revise a registered input, remove
its derived results first, use `replace` with a separate source, then register the
newly generated results with `--derived-from`. Use `remove` for obsolete payloads.
Validate and export a new package after edits; old exports remain unchanged.
See [editing and recovery](../editing.md) and the [workflow diagram](../diagrams/lifecycle.md).
