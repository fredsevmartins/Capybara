"""Local stdio MCP server. All paths are relative to one configured workspace."""

import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .experiments import add_file, bounded, load
from .experiments import create_experiment as create
from .experiments import inspect_experiment as inspect
from .models import Role
from .packages import export_experiment as export
from .packages import import_experiment as import_package
from .validation import validate_experiment as validate


def make_server(workspace: Path) -> FastMCP:
    workspace = Path(workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    server = FastMCP("OpenRepro", instructions="Integrity validation is not scientific validation.")

    def run(action):
        try:
            return {"ok": True, "result": action()}
        except (ValueError, OSError):
            return {
                "ok": False,
                "error": "Invalid input, inaccessible path, or invalid package. "
                "Use relative paths within the configured workspace and validate inputs.",
            }

    @server.tool(structured_output=True)
    def create_experiment(
        path: str, title: str, description: str, authors: list[str], reproduction: str = ""
    ) -> dict[str, Any]:
        """Create a new experiment at a relative workspace path; never overwrite."""
        return run(
            lambda: create(
                bounded(workspace, path), title, description, authors, reproduction=reproduction
            ).model_dump(mode="json")
        )

    @server.tool(structured_output=True)
    def add_experiment_file(
        path: str,
        source: str,
        role: Role,
        description: str = "",
        derived_from: list[str] | None = None,
    ) -> dict[str, Any]:
        """Copy a file inside the configured workspace into an experiment; preserve source."""
        return run(
            lambda: add_file(
                bounded(workspace, path),
                bounded(workspace, source),
                role,
                description,
                derived_from,
            ).model_dump(mode="json")
        )

    @server.tool(structured_output=True)
    def list_experiments() -> dict[str, Any]:
        """List immediate experiment directories in the configured workspace."""

        def action():
            return [
                {"path": p.parent.name, "title": load(bounded(workspace, p.parent.name)).title}
                for p in sorted(workspace.glob("*/manifest.json"))
            ]

        return run(action)

    @server.tool(structured_output=True)
    def inspect_experiment(path: str) -> dict[str, Any]:
        """Return metadata, file roles, descriptions, relationships and validation status."""
        return run(lambda: inspect(bounded(workspace, path)))

    @server.tool(structured_output=True)
    def validate_experiment(path: str) -> dict[str, Any]:
        """Validate metadata and SHA-256 integrity; does not establish scientific validity."""
        return run(lambda: validate(bounded(workspace, path)))

    @server.tool(structured_output=True)
    def export_experiment(path: str, output: str) -> dict[str, Any]:
        """Export a deterministic ZIP package to a new relative workspace path."""

        def action():
            export(bounded(workspace, path), bounded(workspace, output))
            return {"package": output}

        return run(action)

    @server.tool(structured_output=True)
    def import_experiment(package: str, destination: str) -> dict[str, Any]:
        """Validate and import a package into a new workspace directory; never execute files."""

        def action():
            import_package(bounded(workspace, package), bounded(workspace, destination))
            return {"workspace": destination}

        return run(action)

    @server.tool(structured_output=True)
    def list_experiment_files(path: str) -> dict[str, Any]:
        """List inventoried files and checksums without exposing machine-specific paths."""
        return run(
            lambda: [f.model_dump(mode="json") for f in load(bounded(workspace, path)).files]
        )

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenRepro local MCP server (stdio only)")
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    make_server(args.workspace).run(transport="stdio")


if __name__ == "__main__":
    main()
