"""Render/check exact CLI help and supported Python signatures from installed source."""

import argparse
import inspect
from pathlib import Path

from openrepro import __version__, api
from openrepro.cli import parser

ROOT = Path(__file__).resolve().parents[1]
RETURNS = {
    "add_file": "FileEntry; copies and registers a source file, preserving the original.",
    "build_environment": "dict; image/build/cache identities. Requires allow_build=True.",
    "citation": "dict; CSL citation, content identity and DOI only when declared.",
    "compare_results": "dict; status and per-output comparisons. No execution or Docker.",
    "convert_crate": "dict; conversion status and destination. Preserves original metadata.",
    "create_experiment": "Manifest; creates a new workspace and required documents.",
    "create_recipe": "dict; writes a new assisted recipe. Does not execute it.",
    "deposit_bundle": "dict; local bundle identity/status; no upload or assigned DOI.",
    "doctor": "dict; status and prerequisite checks; docker=True also checks the local daemon.",
    "environment_plan": "dict; registered dependency hashes and build plan; no build.",
    "export_experiment": "Path; new deterministic .orepro outside the workspace.",
    "fetch_package": "dict; verified package import into a new destination.",
    "import_experiment": "Path; newly imported, structurally validated workspace.",
    "inspect_experiment": "dict; metadata, file inventory and validation.",
    "lock_environment": "dict; registered wheels/hash lock; requires allow_download=True.",
    "publish_package": "dict; immutable local catalog record/revision; not Internet publication.",
    "recover_run": "dict; recovery/cancellation state for the matching labelled interrupted run.",
    "remove_file": "None; removes a registered payload and records provenance.",
    "render_report": "dict; report path and run status; writes escaped standalone HTML.",
    "replace_file": "FileEntry; revises registered bytes with rollback and provenance.",
    "reproduce": "dict; run status, image, logs and comparisons; explicit execution.",
    "reproduction_plan": "dict; validated recipe/input identities, without execution.",
    "search_catalog": "list[dict]; bounded metadata search of immutable revisions.",
    "update_metadata": "Manifest; updated descriptive metadata; identity/inventory preserved.",
    "validate_experiment": "dict; PASS/WARN/FAIL, issues and scientific_validity=NOT_EVALUATED.",
    "zenodo_deposit": "dict; reconciled journal; publish=True explicitly requests publication.",
}


def rendered():
    cli_parser = parser()
    cli_parser.formatter_class = lambda prog: argparse.HelpFormatter(prog, width=80)
    cli = [
        "# Complete CLI options\n",
        f"Generated from the installed {__version__} parser. Do not edit help blocks by hand.\n"
        "Regenerate with `python scripts/documentation_reference.py --write`.\n"
        "See [CLI behavior and exit codes](cli-reference.md) for interpretation.\n",
        "## Top-level help\n\n```text\n" + cli_parser.format_help().rstrip() + "\n```\n",
    ]
    choices = next(
        a.choices for a in cli_parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    for command, subparser in choices.items():
        subparser.formatter_class = lambda prog: argparse.HelpFormatter(prog, width=80)
        cli.append(f"## {command}\n\n```text\n{subparser.format_help().rstrip()}\n```\n")
    reference = [
        "# Supported Python API reference\n",
        "Generated signatures from `openrepro.api`. Follow the [API tutorial](python-api.md)\n"
        "for runnable code and error handling. All filesystem paths are `pathlib.Path`.\n"
        "Use fresh destinations and a single trusted writer. Operations can raise\n"
        "`OpenReproError` (a `ValueError`), validation errors or filesystem exceptions.\n"
        "Functions returning a report can report FAIL without raising: inspect status.\n",
    ]
    for name in api.__all__:
        value = getattr(api, name)
        reference.append(f"## {name}\n")
        if inspect.isclass(value):
            reference.append(
                f"`openrepro.api.{name}`\n\n"
                + (
                    "Application error; catch before generic ValueError.\n"
                    if name == "OpenReproError"
                    else "Role enumeration; see [file roles](package-format.md).\n"
                    if name == "Role"
                    else "Pydantic model; validate with `model_validate`, serialize with "
                    '`model_dump(mode="json")`. See [schemas](schemas/README.md) '
                    "and [package format](package-format.md).\n"
                )
            )
        else:
            reference.append(
                f"```python\n{name}{inspect.signature(value)}\n```\n\n{RETURNS[name]}\n"
            )
    return {"docs/cli-options.md": "\n".join(cli), "docs/api-reference.md": "\n".join(reference)}


def check_references():
    for name, expected in rendered().items():
        if (ROOT / name).read_text(encoding="utf-8") != expected:
            raise ValueError(f"Stale reference: {name}; run documentation_reference.py --write")


if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--write", action="store_true")
    if arguments.parse_args().write:
        for name, content in rendered().items():
            (ROOT / name).write_text(content, encoding="utf-8")
    else:
        check_references()
    print("CLI options and supported Python API references are current")
