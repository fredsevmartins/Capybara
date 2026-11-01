"""Recipe validation and independent comparison, without Docker."""

import json

import pytest

from openrepro.experiments import add_file, create_experiment
from openrepro.models import OpenReproError, Role
from openrepro.reproduction import Comparison, Recipe, compare_results, reproduce, reproduction_plan

IMAGE = "sha256:" + "a" * 64


@pytest.fixture
def comparison_study(tmp_path):
    root = tmp_path / "study"
    create_experiment(root, "Study", "Synthetic", ["A"])
    source = tmp_path / "reference.json"
    source.write_text('{"value": [1.0, 2.0], "unit": "mg", "valid": true}')
    entry = add_file(root, source, Role.table)
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    return root, outputs, entry.path


@pytest.mark.parametrize(
    "actual, expected",
    [
        ('{"value":[1.00000001,2],"unit":"mg","valid":true}', "PASS"),
        ('{"value":[1.1,2],"unit":"mg","valid":true}', "FAIL"),
        ('{"value":[1,2],"unit":"g","valid":true}', "FAIL"),
        ('{"value":[1,2],"unit":"mg","valid":1}', "FAIL"),
        ('{"value":[1,2],"unit":"mg","valid":true,"extra":0}', "FAIL"),
        ('{"value":[1],"unit":"mg","valid":true}', "FAIL"),
        ('{"value":[NaN,2],"unit":"mg","valid":true}', "FAIL"),
        ('{"value":[1,2],"value":[1,2],"unit":"mg","valid":true}', "FAIL"),
        ("broken", "FAIL"),
        ('1,"extra":2', "FAIL"),
    ],
)
def test_numeric_comparison(comparison_study, actual, expected):
    root, outputs, reference = comparison_study
    (outputs / "result.json").write_text(actual)
    result = compare_results(
        root, outputs, [Comparison(reference=reference, output="result.json", mode="json-numeric")]
    )
    assert result["status"] == expected
    assert result["scientific_validity"] == "NOT_EVALUATED"


def test_exact_and_missing_output(comparison_study):
    root, outputs, reference = comparison_study
    comparison = Comparison(reference=reference, output="result.json")
    assert compare_results(root, outputs, [comparison])["status"] == "FAIL"
    (outputs / "result.json").write_bytes((root / reference).read_bytes())
    assert compare_results(root, outputs, [comparison])["status"] == "PASS"
    (outputs / "result.json").write_bytes((root / reference).read_bytes() + b"\n")
    assert compare_results(root, outputs, [comparison])["status"] == "FAIL"


@pytest.mark.parametrize(
    "changes",
    [
        {"image": "python:latest"},
        {"image": "--privileged"},
        {"command": []},
        {"command": ["\x00"]},
        {"comparisons": []},
        {"timeout_seconds": 0},
        {"timeout_seconds": 3601},
        {"memory_mb": 99999},
        {"cpus": float("nan")},
        {"schema_version": "9"},
        {"dependency_files": ["../escape"]},
    ],
)
def test_invalid_recipes(changes):
    data = dict(
        image=IMAGE,
        command=["python", "analysis/scripts/run.py"],
        comparisons=[{"reference": "results/result.json", "output": "result.json"}],
    )
    data.update(changes)
    with pytest.raises(ValueError):
        Recipe.model_validate(data)


@pytest.mark.parametrize(
    "changes",
    [
        {"output": "../escape"},
        {"reference": "/absolute"},
        {"mode": "python"},
        {"relative_tolerance": -1},
        {"absolute_tolerance": float("inf")},
    ],
)
def test_invalid_comparison(changes):
    data = dict(reference="results/ref.json", output="result.json")
    data.update(changes)
    with pytest.raises(ValueError):
        Comparison.model_validate(data)


def test_plan_and_execution_opt_in(comparison_study, tmp_path):
    root, outputs, reference = comparison_study
    recipe = Recipe(
        image=IMAGE,
        command=["python", "analysis/scripts/run.py"],
        comparisons=[Comparison(reference=reference, output="result.json")],
        dependency_files=[reference],
    )
    plan = reproduction_plan(root, recipe)
    assert plan["dependencies"][0]["sha256"]
    assert plan["execution_required"]
    with pytest.raises(OpenReproError, match="explicitly allow"):
        reproduce(root, recipe, tmp_path / "run")
    assert not (tmp_path / "run").exists()
    recipe.dependency_files = ["missing.lock"]
    with pytest.raises(OpenReproError, match="must be registered"):
        reproduction_plan(root, recipe)


def test_symlink_and_size_rejection(comparison_study, tmp_path, monkeypatch):
    from openrepro import reproduction

    root, outputs, reference = comparison_study
    outside = tmp_path / "outside"
    outside.write_text("secret")
    try:
        (outputs / "result.json").symlink_to(outside)
    except OSError:
        pytest.skip("Symlinks unavailable")
    comparison = Comparison(reference=reference, output="result.json")
    assert compare_results(root, outputs, [comparison])["status"] == "FAIL"
    (outputs / "result.json").unlink()
    (outputs / "result.json").write_text("large")
    monkeypatch.setattr(reproduction, "MAX_RESULT_BYTES", 1)
    assert compare_results(root, outputs, [comparison])["status"] == "FAIL"


def test_cli_plan_and_compare(comparison_study, tmp_path):
    from test_interfaces import cli

    root, outputs, reference = comparison_study
    spec = tmp_path / "recipe.json"
    spec.write_text(
        json.dumps(
            dict(
                image=IMAGE,
                command=["python", "/experiment/run.py"],
                comparisons=[dict(reference=reference, output="result.json")],
            )
        )
    )
    assert cli("plan", root, "--spec", spec, "--json")["execution_required"]
    cli("compare", root, "--spec", spec, "--outputs", outputs, "--json", expected=1)
    (outputs / "result.json").write_bytes((root / reference).read_bytes())
    assert cli("compare", root, "--spec", spec, "--outputs", outputs, "--json")["status"] == "PASS"
    cli("reproduce", root, "--spec", spec, "--output", tmp_path / "run", "--json", expected=2)


@pytest.mark.parametrize("missing", ["memory", "swap", "pids", "cpu", "security"])
def test_missing_isolation_support_fails_closed(comparison_study, tmp_path, monkeypatch, missing):
    import subprocess

    from openrepro import reproduction

    root, outputs, reference = comparison_study
    monkeypatch.setattr(reproduction.platform, "system", lambda: "Linux")
    capabilities = dict(
        memory=True,
        swap=True,
        pids=True,
        cpu=True,
        security=["name=seccomp,profile=builtin"],
        version="test",
    )
    capabilities[missing] = [] if missing == "security" else False
    calls = []

    def docker(*args, **kwargs):
        calls.append(args)
        assert args[0] == "info", "Must not inspect/create/start after a missing requirement"
        return subprocess.CompletedProcess([], 0, stdout=json.dumps(capabilities))

    monkeypatch.setattr(reproduction, "_docker", docker)
    spec = Recipe(
        image=IMAGE,
        command=["python", "-c", "pass"],
        comparisons=[Comparison(reference=reference, output="result.json")],
    )
    with pytest.raises(OpenReproError, match="must support"):
        reproduce(root, spec, tmp_path / "run", allow_execution=True)
    assert len(calls) == 1
    assert not (tmp_path / "run").exists()
