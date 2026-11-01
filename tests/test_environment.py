"""Locked environment inputs and fail-closed build validation."""

import pytest

from openrepro.environment import (
    EnvironmentSpec,
    build_environment,
    environment_plan,
    lock_environment,
)
from openrepro.experiments import add_file, create_experiment
from openrepro.models import OpenReproError, Role

IMAGE = "sha256:" + "a" * 64


@pytest.fixture
def environment_study(tmp_path):
    root = tmp_path / "study"
    create_experiment(root, "Environment", "D", ["A"])
    source = tmp_path / "requirements.lock"
    source.write_text("example==1.0 --hash=sha256:" + "b" * 64 + "\n")
    lock = add_file(root, source, Role.supplementary)
    source = tmp_path / "example-1.0-py3-none-any.whl"
    source.write_bytes(b"not executed by planning")
    wheel = add_file(root, source, Role.supplementary)
    return root, EnvironmentSpec(base_image=IMAGE, requirements=lock.path, wheels=[wheel.path])


def test_environment_fingerprint_and_registered_inputs(environment_study):
    root, spec = environment_study
    first = environment_plan(root, spec)
    assert environment_plan(root, spec) == first
    assert len(first["fingerprint"]) == 64
    assert len(first["inputs"]) == 2
    with pytest.raises(OpenReproError, match="explicitly allow"):
        build_environment(root, spec)
    spec.wheels = ["supplementary/missing.whl"]
    with pytest.raises(OpenReproError, match="registered"):
        environment_plan(root, spec)


@pytest.mark.parametrize(
    "changes",
    [
        {"base_image": "python:latest"},
        {"requirements": "../escape", "wheels": ["a.whl"]},
        {"requirements": "requirements.lock"},
        {"wheels": ["a.whl"]},
        {"requirements": "requirements.lock", "wheels": ["a.tar.gz"]},
        {"requirements": "requirements.lock", "wheels": ["a/x.whl", "b/X.whl"]},
        {"schema_version": "2"},
    ],
)
def test_bad_environment_specs(changes):
    values = dict(base_image=IMAGE)
    values.update(changes)
    with pytest.raises(ValueError):
        EnvironmentSpec.model_validate(values)


def test_download_is_explicit(environment_study, tmp_path):
    root, _ = environment_study
    with pytest.raises(OpenReproError, match="explicit download"):
        lock_environment(root, "supplementary/requirements.in", IMAGE, tmp_path / "resolved")
    assert not (tmp_path / "resolved").exists()
