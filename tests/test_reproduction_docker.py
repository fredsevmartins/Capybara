"""Opt-in integration against a real local Docker daemon and Python image."""

import json
import os

import pytest

from openrepro.experiments import add_file, create_experiment, digest
from openrepro.models import OpenReproError, Role
from openrepro.reproduction import Comparison, Recipe, _docker, reproduce

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENREPRO_TEST_IMAGE"),
    reason="Set OPENREPRO_TEST_IMAGE to a local Python image ID",
)


@pytest.fixture
def execution_study(tmp_path):
    root = tmp_path / "study"
    create_experiment(root, "Execution demo", "Synthetic", ["A"])
    reference = tmp_path / "reference.json"
    reference.write_text('{"value": 4.0}')
    entry = add_file(root, reference, Role.table)
    return root, entry.path


def recipe(reference, script, **options):
    return Recipe(
        image=os.environ["OPENREPRO_TEST_IMAGE"],
        command=["python", "-c", script],
        comparisons=[Comparison(reference=reference, output="result.json", mode="json-numeric")],
        **options,
    )


def test_real_execution_and_isolation(execution_study, tmp_path, monkeypatch):
    root, reference = execution_study
    before = digest(root / "manifest.json")
    monkeypatch.setenv("OPENREPRO_HOST_SECRET", "must-not-enter-container")
    script = """
import json, os, socket
from pathlib import Path
assert os.getuid() != 0
assert 'OPENREPRO_HOST_SECRET' not in os.environ
assert not os.environ.get('HTTPS_PROXY')
assert not Path('/var/run/docker.sock').exists()
assert [name for _, name in socket.if_nameindex()] == ['lo']
try:
    Path('/experiment/README.md').write_text('changed')
except OSError:
    pass
else:
    raise AssertionError('experiment is writable')
Path('/output/result.json').write_text(json.dumps({'value': 2 * 2}))
print('analysis completed')
"""
    run = tmp_path / "run"
    result = reproduce(root, recipe(reference, script), run, allow_execution=True)
    assert result["status"] == "PASS"
    assert result["exit_code"] == 0
    assert not result["timed_out"]
    assert result["image"]["id"] == os.environ["OPENREPRO_TEST_IMAGE"]
    assert result["recipe_sha256"]
    assert json.loads((run / "report.json").read_text()) == result
    assert (run / "outputs/result.json").is_file()
    assert "analysis completed" in (run / "stdout.txt").read_text()
    assert digest(root / "manifest.json") == before
    assert not (run / "experiment").exists()
    assert not list(tmp_path.glob(".openrepro-run-*"))


@pytest.mark.parametrize(
    "script,options,timed_out,exit_code",
    [
        ("raise SystemExit(7)", {}, False, 7),
        ("import time; time.sleep(30)", {"timeout_seconds": 1}, True, None),
        (
            "from pathlib import Path; Path('/output/result.json').write_text('{\"value\": 99}')",
            {},
            False,
            0,
        ),
    ],
)
def test_execution_failures(execution_study, tmp_path, script, options, timed_out, exit_code):
    root, reference = execution_study
    result = reproduce(
        root, recipe(reference, script, **options), tmp_path / "run", allow_execution=True
    )
    assert result["status"] == "FAIL"
    assert result["timed_out"] is timed_out
    assert result["exit_code"] == exit_code
    assert (
        _docker("ps", "--all", "--filter", "name=openrepro-", "--format", "{{.Names}}").stdout == ""
    )


def test_unsafe_outputs_are_not_retained(execution_study, tmp_path):
    root, reference = execution_study
    script = "from pathlib import Path; Path('/output/result.json').symlink_to('/etc/passwd')"
    with pytest.raises(OpenReproError, match="Unsafe output"):
        reproduce(root, recipe(reference, script), tmp_path / "run", allow_execution=True)
    assert not (tmp_path / "run").exists()


def test_existing_destination_is_preserved(execution_study, tmp_path):
    root, reference = execution_study
    destination = tmp_path / "run"
    destination.mkdir()
    (destination / "keep").write_text("preserve")
    with pytest.raises(OpenReproError, match="already exists"):
        reproduce(root, recipe(reference, "pass"), destination, allow_execution=True)
    assert (destination / "keep").read_text() == "preserve"


def test_packaged_analysis_roundtrip(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    from openrepro.packages import import_experiment

    checkout = Path(__file__).resolve().parents[1]
    example = tmp_path / "example"
    subprocess.run(
        [
            sys.executable,
            str(checkout / "examples/reproduction/generate.py"),
            "--output",
            str(example),
            "--image",
            os.environ["OPENREPRO_TEST_IMAGE"],
        ],
        check=True,
    )
    root = import_experiment(example / "experiment.orepro", tmp_path / "received")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "openrepro.cli",
            "reproduce",
            str(root),
            "--spec",
            str(example / "recipe.json"),
            "--output",
            str(tmp_path / "run"),
            "--allow-execution",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(completed.stdout)
    assert report["status"] == "PASS"
    assert report["dependencies"][0]["path"] == "supplementary/requirements.txt"
    summary = json.loads((tmp_path / "run/outputs/summary.json").read_text())
    assert summary["count"] == 4
    assert summary["mean"] == 2.5
    assert summary["sample_sd"] == pytest.approx(1.2909944487358056)


def test_non_utf8_analysis_logs(execution_study, tmp_path):
    root, reference = execution_study
    script = (
        "import os; from pathlib import Path; os.write(1, bytes([255])); "
        "Path('/output/result.json').write_text('{\"value\": 4}')"
    )
    result = reproduce(root, recipe(reference, script), tmp_path / "run", allow_execution=True)
    assert result["status"] == "PASS"
    assert "\ufffd" in (tmp_path / "run/stdout.txt").read_text(encoding="utf-8")
