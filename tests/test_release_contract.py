"""Public API, committed-package compatibility and machine-readable schema contracts."""

import json
from pathlib import Path

import pytest

from openrepro import api
from openrepro.environment import EnvironmentSpec
from openrepro.models import Manifest
from openrepro.reproduction import Recipe
from openrepro.validation import validate_experiment


@pytest.mark.parametrize("name", ["pharmacokinetics", "dissolution", "statistics"])
def test_legacy_package_import_and_reexport(name, tmp_path):
    checkout = Path(__file__).resolve().parents[1]
    root = api.import_experiment(checkout / "examples/packages" / f"{name}.orepro", tmp_path / name)
    assert validate_experiment(root)["status"] == "PASS"
    package = api.export_experiment(root, tmp_path / "again.orepro")
    restored = api.import_experiment(package, tmp_path / "restored")
    assert api.inspect_experiment(restored)["metadata"] == api.inspect_experiment(root)["metadata"]


@pytest.mark.parametrize(
    "kind,model,version",
    [
        ("manifest", Manifest, "0.1"),
        ("recipe", Recipe, "0.2"),
        ("environment", EnvironmentSpec, "1"),
    ],
)
def test_schema_cli_and_fixed_versions(kind, model, version, tmp_path):
    from test_interfaces import cli

    output = tmp_path / "schema.json"
    cli("schema", "--kind", kind, "--output", output, "--json")
    schema = json.loads(output.read_text())
    assert schema == model.model_json_schema()
    assert schema["properties"]["schema_version"]["const"] == version
    assert schema["additionalProperties"] is False


def test_supported_api_exports_are_importable():
    assert {
        "create_experiment",
        "reproduce",
        "publish_package",
        "zenodo_deposit",
        "convert_crate",
    } <= set(api.__all__)
    for name in api.__all__:
        assert getattr(api, name) is not None
