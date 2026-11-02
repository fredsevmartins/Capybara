"""Check documentation links, schema/reference freshness and executable tutorials."""

import argparse
import json
import re
from pathlib import Path

from check_documented_examples import check_examples
from documentation_reference import check_references

from openrepro.cli import parser
from openrepro.environment import EnvironmentSpec
from openrepro.models import Manifest
from openrepro.reproduction import Recipe

root = Path(__file__).resolve().parents[1]
count = 0
pages = [
    *sorted(root.glob("*.md")),
    *sorted((root / "docs").rglob("*.md")),
    root / "examples/iris/README.md",
]
for path in pages:
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if "://" not in target and not target.startswith("#"):
            if not (path.parent / target.split("#")[0]).exists():
                raise ValueError(f"Broken local link: {path.relative_to(root)} -> {target}")
            count += 1
    for target in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', text):
        if "://" not in target and not (path.parent / target).is_file():
            raise ValueError(f"Missing image: {path.relative_to(root)} -> {target}")
for path in sorted((root / "docs/diagrams").glob("*.mmd")):
    source = path.read_text(encoding="utf-8").strip()
    if f"```mermaid\n{source}\n```" not in path.with_suffix(".md").read_text(encoding="utf-8"):
        raise ValueError(f"Stale mirrored diagram: {path.name}")
commands = next(
    action.choices for action in parser()._actions if isinstance(action, argparse._SubParsersAction)
)
reference = (root / "docs/cli-reference.md").read_text(encoding="utf-8")
for command in commands:
    if f"`{command}" not in reference:
        raise ValueError(f"Undocumented CLI command: {command}")
for kind, model in (("manifest", Manifest), ("recipe", Recipe), ("environment", EnvironmentSpec)):
    if (
        json.loads((root / f"docs/schemas/{kind}.schema.json").read_text())
        != model.model_json_schema()
    ):
        raise ValueError(f"Stale documented JSON schema: {kind}")
check_references()
check_examples()
print(
    f"Checked {len(pages)} pages, {count} local links, diagrams, schemas "
    f"and {len(commands)} commands"
)
