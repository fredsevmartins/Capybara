"""Check local documentation links, mirrored Mermaid sources and CLI usage."""

import argparse
import re
from pathlib import Path

from openrepro.cli import parser

root = Path(__file__).resolve().parents[1]
count = 0
for path in [root / "README.md", *sorted((root / "docs").rglob("*.md"))]:
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if "://" not in target and not target.startswith("#"):
            assert (path.parent / target.split("#")[0]).exists(), (path, target)
            count += 1
for path in sorted((root / "docs/diagrams").glob("*.mmd")):
    source = path.read_text().strip()
    assert f"```mermaid\n{source}\n```" in path.with_suffix(".md").read_text()
commands = next(
    action.choices for action in parser()._actions if isinstance(action, argparse._SubParsersAction)
)
reference = (root / "docs/cli-reference.md").read_text(encoding="utf-8")

for command in commands:
    assert command in parser().format_help()
    assert f"`{command}" in reference, ("Undocumented CLI command", command)
print(f"Checked {count} local links, six mirrored Mermaid sources and {len(commands)} CLI commands")
