"""Command-line interface using the standard library."""

import argparse
import json
import sqlite3
from pathlib import Path

from . import __version__
from .experiments import (
    add_file,
    create_experiment,
    inspect_experiment,
    load,
    remove_file,
    replace_file,
    update_metadata,
)
from .models import Role
from .packages import export_experiment, import_experiment
from .validation import validate_experiment


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="openrepro", description="Share experiments. Reproduce science."
    )
    sub = p.add_subparsers(dest="command", required=True)
    for command in (
        "init",
        "add",
        "list",
        "inspect",
        "validate",
        "export",
        "import",
        "version",
        "update",
        "remove",
        "replace",
        "plan",
        "reproduce",
        "compare",
        "environment-lock",
        "environment-build",
        "recipe",
        "doctor",
        "report",
        "recover",
        "publish",
        "search",
        "fetch",
        "cite",
        "serve",
        "deposit-bundle",
        "zenodo-deposit",
        "convert-crate",
        "schema",
    ):
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
        elif command not in ("version", "schema"):
            s.add_argument("path", type=Path)
        if command in ("plan", "reproduce", "compare"):
            s.add_argument(
                "--spec", required=True, type=Path, help="Reviewed reproduction recipe JSON"
            )
        if command == "reproduce":
            s.add_argument(
                "--environment", type=Path, help="Build from a registered environment lock"
            )
            s.add_argument("--allow-build", action="store_true")
            s.add_argument("--output", required=True, type=Path, help="New external run directory")
            s.add_argument(
                "--allow-execution", action="store_true", help="Explicitly execute reviewed code"
            )
        if command == "compare":
            s.add_argument(
                "--outputs", required=True, type=Path, help="Directory of regenerated outputs"
            )
        if command == "update":
            s.add_argument(
                "--metadata", required=True, type=Path, help="JSON object of metadata changes"
            )
        if command in ("remove", "replace"):
            s.add_argument("file", help="Registered relative file path")
        if command == "replace":
            s.add_argument("source", type=Path)
        if command == "add":
            s.add_argument("source", type=Path)
            s.add_argument("--role", choices=[r.value for r in Role], required=True)
            s.add_argument("--description", default="")
            s.add_argument("--derived-from", action="append", default=[])
        if command == "schema":
            s.add_argument("--kind", choices=("manifest", "recipe", "environment"), required=True)
            s.add_argument("--output", type=Path, required=True)
        if command == "environment-lock":
            s.add_argument("--requirements", required=True, help="Registered requirements input")
            s.add_argument("--base-image", required=True, help="Reviewed immutable base image ID")
            s.add_argument("--output", required=True, type=Path)
            s.add_argument("--allow-download", action="store_true")
        if command == "environment-build":
            s.add_argument("--spec", required=True, type=Path)
            s.add_argument("--allow-build", action="store_true")
        if command == "recipe":
            s.add_argument("--image", required=True)
            s.add_argument("--output", required=True, type=Path)
            s.add_argument("--script")
            s.add_argument("--interpreter", default="python")
            s.add_argument("--reference")
            s.add_argument("--result-name")
        if command == "doctor":
            s.add_argument("--docker", action="store_true")
        if command in ("report", "deposit-bundle", "convert-crate"):
            s.add_argument("--output", required=True, type=Path)
        if command == "convert-crate":
            s.add_argument("--license")
            s.add_argument("--author", action="append")
        if command == "publish":
            s.add_argument("--catalog", required=True, type=Path)
        if command == "search":
            s.add_argument("--query", default="")
            s.add_argument("--limit", type=int, default=20)
            s.add_argument("--experiment")
        if command in ("fetch", "cite"):
            s.add_argument("checksum")
        if command == "fetch":
            s.add_argument("destination", type=Path)
        if command == "serve":
            s.add_argument("--host", default="127.0.0.1")
            s.add_argument("--port", type=int, default=8080)
        if command == "zenodo-deposit":
            s.add_argument(
                "--publish", action="store_true", help="Publicly publish the reviewed deposit"
            )
            s.add_argument("--deposition-id", type=int)
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
        elif c == "schema":
            from .environment import EnvironmentSpec
            from .experiments import json_bytes
            from .models import Manifest
            from .reproduction import Recipe

            models = {"manifest": Manifest, "recipe": Recipe, "environment": EnvironmentSpec}
            with args.output.open("xb") as stream:
                stream.write(json_bytes(models[args.kind].model_json_schema()))
            result = {"schema": str(args.output), "kind": args.kind}
        elif c in ("environment-lock", "environment-build"):
            from .environment import EnvironmentSpec, build_environment, lock_environment
            from .experiments import load_json

            if c == "environment-lock":
                result = lock_environment(
                    args.path,
                    args.requirements,
                    args.base_image,
                    args.output,
                    allow_download=args.allow_download,
                )
            else:
                spec = EnvironmentSpec.model_validate(load_json(args.spec))
                result = build_environment(args.path, spec, allow_build=args.allow_build)
        elif c in ("recipe", "doctor", "report"):
            from .experience import create_recipe, doctor, render_report

            if c == "recipe":
                result = create_recipe(
                    args.path,
                    args.image,
                    args.output,
                    script=args.script,
                    reference=args.reference,
                    output=args.result_name,
                    interpreter=args.interpreter,
                )
            elif c == "doctor":
                result = doctor(args.path, docker=args.docker)
            else:
                result = render_report(args.path, args.output)
        elif c == "recover":
            from .reproduction import recover_run

            result = recover_run(args.path)
        elif c in ("publish", "search", "fetch", "cite", "serve"):
            from .catalog import (
                catalog_server,
                citation,
                fetch_package,
                publish_package,
                search_catalog,
            )

            if c == "publish":
                result = publish_package(args.path, args.catalog)
            elif c == "search":
                result = {
                    "packages": search_catalog(
                        args.path, args.query, limit=args.limit, experiment=args.experiment
                    )
                }
            elif c == "fetch":
                result = fetch_package(args.path, args.checksum, args.destination)
            elif c == "cite":
                result = citation(args.path, args.checksum)
            else:
                with catalog_server(args.path, args.host, args.port) as server:
                    try:
                        server.serve_forever()
                    except KeyboardInterrupt:
                        return
        elif c in ("deposit-bundle", "zenodo-deposit"):
            from .zenodo import deposit_bundle, zenodo_deposit

            result = (
                deposit_bundle(args.path, args.output)
                if c == "deposit-bundle"
                else zenodo_deposit(
                    args.path, publish=args.publish, deposition_id=args.deposition_id
                )
            )
        elif c == "convert-crate":
            from .interoperability import convert_crate

            result = convert_crate(
                args.path, args.output, license=args.license, authors=args.author
            )
        elif c in ("plan", "reproduce", "compare"):
            from .experiments import load_json
            from .reproduction import Recipe, compare_results, reproduce, reproduction_plan

            recipe = Recipe.model_validate(load_json(args.spec))
            if c == "plan":
                result = reproduction_plan(args.path, recipe)
            elif c == "compare":
                result = compare_results(args.path, args.outputs, recipe.comparisons)
            else:
                environment = None
                if not args.allow_execution:
                    from .models import OpenReproError

                    raise OpenReproError("Review the recipe and explicitly allow execution")
                if args.environment:
                    from .environment import EnvironmentSpec, build_environment
                    from .reproduction import Recipe

                    environment_spec = EnvironmentSpec.model_validate(load_json(args.environment))
                    environment = build_environment(
                        args.path, environment_spec, allow_build=args.allow_build
                    )
                    values = recipe.model_dump()
                    values["image"] = environment["image"]
                    values["dependency_files"] = sorted(
                        set(recipe.dependency_files) | set(environment["inputs"])
                    )
                    recipe = Recipe.model_validate(values)
                result = reproduce(
                    args.path, recipe, args.output, allow_execution=args.allow_execution
                )
                if environment is not None:
                    from .experiments import atomic_write, json_bytes

                    result["environment_build"] = environment
                    atomic_write(args.output / "report.json", json_bytes(result))
        elif c == "update":
            from .experiments import load_json

            result = update_metadata(args.path, load_json(args.metadata)).model_dump(mode="json")
        elif c == "remove":
            remove_file(args.path, args.file)
            result = {"removed": args.file}
        elif c == "replace":
            result = replace_file(args.path, args.file, args.source).model_dump(mode="json")
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
        if (
            c in ("validate", "compare", "reproduce", "doctor", "report")
            and result["status"] == "FAIL"
        ):
            raise SystemExit(1)
    except (ValueError, OSError, sqlite3.Error, RecursionError) as exc:
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
