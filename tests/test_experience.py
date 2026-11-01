"""Guided recipes and reports must remain non-executing and HTML-safe."""

import json

import pytest

from openrepro.experience import create_recipe, doctor, render_report
from openrepro.experiments import add_file, create_experiment
from openrepro.models import OpenReproError, Role
from openrepro.reproduction import Recipe


def test_guided_recipe_and_doctor(tmp_path):
    root = tmp_path / "study"
    create_experiment(root, "T", "D", ["A"])
    script = tmp_path / "analysis.py"
    script.write_text('raise AssertionError("Must not execute during recipe generation")')
    add_file(root, script, Role.script)
    reference = tmp_path / "result.json"
    reference.write_text('{"value":4}')
    add_file(root, reference, Role.table)
    destination = tmp_path / "recipe.json"
    create_recipe(root, "sha256:" + "a" * 64, destination)
    recipe = Recipe.model_validate_json(destination.read_text())
    assert recipe.command == ["python", "analysis/scripts/analysis.py"]
    assert doctor(root)["status"] == "PASS"
    with pytest.raises(FileExistsError):
        create_recipe(root, recipe.image, destination)


def test_report_escapes_analysis_content(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    payload = '<script>alert("analysis")</script>'
    (run / "report.json").write_text(
        json.dumps(
            {
                "status": "FAIL",
                "experiment": payload,
                "comparison": {
                    "comparisons": [
                        {
                            "reference": payload,
                            "status": "FAIL",
                            "mode": "json-numeric",
                            "differences": [{"expected": payload, "actual": "other"}],
                        }
                    ]
                },
            }
        )
    )
    output = tmp_path / "report.html"
    assert render_report(run, output)["status"] == "FAIL"
    page = output.read_text()
    assert payload not in page
    assert "&lt;script&gt;" in page
    assert "Scientific validity was not evaluated" in page
    with pytest.raises(FileExistsError):
        render_report(run, output)


def test_recipe_does_not_guess_ambiguous_inputs(tmp_path):
    root = tmp_path / "study"
    create_experiment(root, "T", "D", ["A"])
    with pytest.raises(OpenReproError, match="Choose --script"):
        create_recipe(root, "sha256:" + "a" * 64, tmp_path / "recipe.json")
