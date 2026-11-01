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


def test_output_filesystem_has_a_real_quota(execution_study, tmp_path):
    root, reference = execution_study
    script = """
from pathlib import Path
large=Path('/output/large.bin')
try:
    large.write_bytes(b'x'*(2*1024*1024))
except OSError as error:
    assert error.errno == 28, error
    print('quota enforced')
else:
    raise AssertionError('No output quota')
large.unlink(missing_ok=True)
Path('/output/result.json').write_text('{"value": 4}')
"""
    result = reproduce(
        root, recipe(reference, script, output_mb=1), tmp_path / "run", allow_execution=True
    )
    assert result["status"] == "PASS"
    assert result["output_quota_mb"] == 1
    assert "quota enforced" in (tmp_path / "run/stdout.txt").read_text()


def test_recovery_cancels_only_the_matching_label(tmp_path):
    from uuid import uuid4

    from openrepro.experiments import json_bytes
    from openrepro.reproduction import recover_run

    run_id = uuid4().hex
    name = "openrepro-" + run_id
    staging = tmp_path / "interrupted"
    staging.mkdir()
    (staging / "journal.json").write_bytes(json_bytes({"run_id": run_id, "state": "running"}))
    try:
        _docker(
            "create",
            "--name",
            name,
            "--label",
            "org.openrepro.run=" + run_id,
            "--network=none",
            "--entrypoint=/bin/sh",
            os.environ["OPENREPRO_TEST_IMAGE"],
            "-c",
            "exec sleep infinity",
        )
        _docker("start", name)
        assert recover_run(staging)["container_removed"]
        assert not recover_run(staging)["container_removed"]
        assert json.loads((staging / "journal.json").read_text())["state"] == "cancelled"
    finally:
        _docker("rm", "--force", name, check=False)


def test_offline_locked_environment_build(execution_study, tmp_path):
    import zipfile

    from openrepro.environment import EnvironmentSpec, build_environment
    from openrepro.experiments import digest

    root, reference = execution_study
    wheel = tmp_path / "openrepro_calibration-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("openrepro_calibration/__init__.py", "value = 4.0\n")
        archive.writestr(
            "openrepro_calibration-1.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: openrepro-calibration\nVersion: 1.0\n",
        )
        archive.writestr(
            "openrepro_calibration-1.0.dist-info/WHEEL",
            "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr("openrepro_calibration-1.0.dist-info/RECORD", "")
    registered_wheel = add_file(root, wheel, Role.supplementary)
    lock = tmp_path / "requirements.lock"
    lock.write_text("openrepro-calibration==1.0 --hash=sha256:" + digest(wheel) + "\n")
    registered_lock = add_file(root, lock, Role.supplementary)
    spec = EnvironmentSpec(
        base_image=os.environ["OPENREPRO_TEST_IMAGE"],
        requirements=registered_lock.path,
        wheels=[registered_wheel.path],
    )
    built = build_environment(root, spec, allow_build=True)
    assert built["image"].startswith("sha256:")
    assert build_environment(root, spec, allow_build=True)["cached"]
    script = (
        "import json,openrepro_calibration; from pathlib import Path; "
        "Path('/output/result.json').write_text(json.dumps({'value':openrepro_calibration.value}))"
    )
    run_recipe = recipe(reference, script).model_copy(update={"image": built["image"]})
    assert reproduce(root, run_recipe, tmp_path / "run", allow_execution=True)["status"] == "PASS"
    bad_lock = tmp_path / "bad.lock"
    bad_lock.write_text("openrepro-calibration==1.0 --hash=sha256:" + "0" * 64 + "\n")
    bad_entry = add_file(root, bad_lock, Role.supplementary)
    bad_spec = EnvironmentSpec(
        base_image=built["image"], requirements=bad_entry.path, wheels=[registered_wheel.path]
    )
    with pytest.raises(OpenReproError):
        build_environment(root, bad_spec, allow_build=True)


def test_iris_real_data_reproduction(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    checkout = Path(__file__).resolve().parents[1]
    destination = tmp_path / "iris"
    subprocess.run(
        [
            sys.executable,
            str(checkout / "examples/iris/generate.py"),
            "--output",
            str(destination),
            "--image",
            os.environ["OPENREPRO_TEST_IMAGE"],
        ],
        check=True,
    )
    spec = Recipe.model_validate_json((destination / "recipe.json").read_text())
    result = reproduce(destination / "experiment", spec, tmp_path / "run", allow_execution=True)
    assert result["status"] == "PASS"
    assert result["comparison"]["comparisons"][0]["units"]["/sepal_length_mean"] == "cm"
    values = json.loads((tmp_path / "run/outputs/summary.json").read_text())
    assert values["sepal_length_mean"]["value"] == pytest.approx(5.843333333333334)
    assert (tmp_path / "run/outputs/count.txt").read_text() == "150\n"


def test_second_analysis_language_is_supported(execution_study, tmp_path):
    root, reference = execution_study
    script = tmp_path / "analyze.sh"
    script.write_text("printf '{\"value\":4}' > /output/result.json\n")
    entry = add_file(root, script, Role.script)
    spec = recipe(reference, "unused").model_copy(update={"command": ["/bin/sh", entry.path]})
    assert reproduce(root, spec, tmp_path / "shell-run", allow_execution=True)["status"] == "PASS"


def test_abrupt_runner_termination_can_be_recovered(execution_study, tmp_path):
    import signal
    import subprocess
    import sys
    import time

    from openrepro.reproduction import recover_run

    root, reference = execution_study
    spec = tmp_path / "recipe.json"
    spec.write_text(recipe(reference, "import time; time.sleep(30)").model_dump_json())
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "openrepro.cli",
            "reproduce",
            str(root),
            "--spec",
            str(spec),
            "--output",
            str(tmp_path / "run"),
            "--allow-execution",
            "--json",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    journal_dir = None
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            candidates = list(tmp_path.glob(".openrepro-run-*"))
            if candidates and (candidates[0] / "journal.json").exists():
                state = json.loads((candidates[0] / "journal.json").read_text())
                name = "openrepro-" + state["run_id"]
                running = _docker("inspect", "--format", "{{.State.Running}}", name, check=False)
                if running.returncode == 0 and running.stdout.strip() == "true":
                    journal_dir = candidates[0]
                    break
            time.sleep(0.1)
        assert journal_dir is not None, "Runner did not create a live recoverable execution"
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
        assert recover_run(journal_dir)["container_removed"]
        assert (journal_dir / "journal.json").exists()
        assert not (tmp_path / "run").exists()
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        for directory in tmp_path.glob(".openrepro-run-*"):
            if (directory / "journal.json").exists():
                recover_run(directory)
