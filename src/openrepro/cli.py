"""Command-line interface using the standard library."""

import argparse
import json
from pathlib import Path

from . import __version__
from .experiments import add_file, create_experiment, inspect_experiment, load
from .models import Role
from .packages import export_experiment, import_experiment
from .validation import validate_experiment


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="openrepro", description="Share experiments. Reproduce science."
    )
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("init", "add", "list", "inspect", "validate", "export", "import", "version"):
        s = sub.add_parser(command, help=f"{command.capitalize()} an experiment or package")
        s.add_argument("--json", action="store_true", help="Print structured JSON")
        if command == "init":
            s.add_argument("path", type=Path)
            s.add_argument("--title", required=True)
            s.add_argument("--description", required=True)
            s.add_argument("--author", action="append", required=True)
            s.add_argument("--license", default="CC-BY-4.0")
            s.add_argument("--reproduction", default="")
        elif command == "list":
            s.add_argument("path", type=Path, help="Directory containing experiment workspaces")
        elif command == "import":
            s.add_argument("package", type=Path)
            s.add_argument("destination", type=Path)
        elif command != "version":
            s.add_argument("path", type=Path)
        if command == "add":
            s.add_argument("source", type=Path)
            s.add_argument("--role", choices=[r.value for r in Role], required=True)
            s.add_argument("--description", default="")
            s.add_argument("--derived-from", action="append", default=[])
        if command == "export":
            s.add_argument("output", type=Path)
    return p


def main() -> None:
    args = parser().parse_args()
    try:
        c = args.command
        if c == "version":
            result = {"version": __version__}
        elif c == "init":
            result = create_experiment(
                args.path,
                args.title,
                args.description,
                args.author,
                license=args.license,
                reproduction=args.reproduction,
            ).model_dump(mode="json")
        elif c == "add":
            result = add_file(
                args.path, args.source, Role(args.role), args.description, args.derived_from
            ).model_dump(mode="json")
        elif c == "inspect":
            result = inspect_experiment(args.path)
        elif c == "validate":
            result = validate_experiment(args.path)
        elif c == "export":
            result = {"package": str(export_experiment(args.path, args.output))}
        elif c == "import":
            result = {"workspace": str(import_experiment(args.package, args.destination))}
        else:
            result = {
                "experiments": [
                    load(p.parent).model_dump(mode="json")
                    for p in sorted(args.path.glob("*/manifest.json"))
                ]
            }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(human(result))
        if c == "validate" and result["status"] == "FAIL":
            raise SystemExit(1)
    except (ValueError, OSError) as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}))
        else:
            print(f"Error: {exc}")
        raise SystemExit(2) from exc


def human(value, depth=0):
    if isinstance(value, dict):
        return "\n".join(
            f"{'  ' * depth}{key}: "
            + ("\n" + human(item, depth + 1) if isinstance(item, (dict, list)) else str(item))
            for key, item in value.items()
        )
    if isinstance(value, list):
        return "\n".join(human(item, depth) for item in value)
    return f"{'  ' * depth}{value}"


if __name__ == "__main__":
    main()
