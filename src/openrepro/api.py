"""Supported Python API. Internal underscore-prefixed helpers are not public contracts."""

from .catalog import citation, fetch_package, publish_package, search_catalog
from .environment import EnvironmentSpec, build_environment, environment_plan, lock_environment
from .experience import create_recipe, doctor, render_report
from .experiments import (
    add_file,
    create_experiment,
    inspect_experiment,
    remove_file,
    replace_file,
    update_metadata,
)
from .interoperability import convert_crate
from .models import FileEntry, Manifest, OpenReproError, Role
from .packages import export_experiment, import_experiment
from .reproduction import (
    Comparison,
    Recipe,
    compare_results,
    recover_run,
    reproduce,
    reproduction_plan,
)
from .validation import validate_experiment
from .zenodo import deposit_bundle, zenodo_deposit

__all__ = [
    "Comparison",
    "EnvironmentSpec",
    "FileEntry",
    "Manifest",
    "OpenReproError",
    "Recipe",
    "Role",
    "add_file",
    "build_environment",
    "citation",
    "compare_results",
    "convert_crate",
    "create_experiment",
    "create_recipe",
    "deposit_bundle",
    "doctor",
    "environment_plan",
    "export_experiment",
    "fetch_package",
    "import_experiment",
    "inspect_experiment",
    "lock_environment",
    "publish_package",
    "recover_run",
    "remove_file",
    "render_report",
    "replace_file",
    "reproduce",
    "reproduction_plan",
    "search_catalog",
    "update_metadata",
    "validate_experiment",
    "zenodo_deposit",
]
