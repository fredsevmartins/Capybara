import importlib.util
from pathlib import Path

import pytest
from scipy.stats import ttest_ind

from openrepro.packages import import_experiment
from openrepro.validation import validate_experiment

spec = importlib.util.spec_from_file_location(
    "generate", Path(__file__).parents[1] / "examples/generate.py"
)
examples = importlib.util.module_from_spec(spec)
spec.loader.exec_module(examples)


def test_pk_reference():
    x, y, r = examples.pharmacokinetics()
    assert x[-1] == 24
    assert y[0] == 5  # 100 mg / 20 L
    assert r["auc_infinity_mg_h_L"] == pytest.approx(25, rel=0.0003)
    assert r["terminal_rate_h_inverse"] == pytest.approx(0.2)
    assert r["half_life_h"] == pytest.approx(3.4657359028)
    assert r["clearance_L_h"] == pytest.approx(4, rel=0.0003)
    assert r["volume_L"] == pytest.approx(20, rel=0.0003)


def test_dissolution_reference():
    _, y, r = examples.dissolution()
    assert y[0] == 0
    assert all(a < b for a, b in zip(y, y[1:]))
    assert r["t50_min"] == pytest.approx(8.664339757)
    assert r["t90_min"] == pytest.approx(28.78231366)
    assert y[-1] == pytest.approx(99.1770252951)


def test_statistics_reference():
    a, b, r = examples.statistics_example()
    reference = ttest_ind(b, a, equal_var=False).confidence_interval()
    assert r["ci95_low"] == pytest.approx(reference.low)
    assert r["ci95_high"] == pytest.approx(reference.high)
    assert examples.statistics_example() == (a, b, r)
    assert r["mean_a"] == pytest.approx(9.70353832055987)


def test_examples_export_import(tmp_path):
    examples.generate(tmp_path / "generated")
    for name in ("pharmacokinetics", "dissolution", "statistics"):
        root = import_experiment(tmp_path / f"generated/{name}.orepro", tmp_path / name)
        assert validate_experiment(root)["status"] == "PASS"
        assert (root / "results/figures/figure.png").stat().st_size > 1000


def test_iris_source_identity_and_independent_reference():
    import csv
    import hashlib
    import json
    from statistics import mean, stdev

    here = Path(__file__).resolve().parents[1] / "examples/iris"
    source = json.loads((here / "source.json").read_text())
    assert hashlib.sha256((here / "iris.csv").read_bytes()).hexdigest() == source["sha256"]
    with (here / "iris.csv").open(newline="") as stream:
        rows = list(csv.reader(stream))[1:]
    assert len(rows) == 150
    reference = json.loads((here / "reference.json").read_text())
    for index, name in enumerate(("sepal_length", "sepal_width", "petal_length", "petal_width")):
        values = [float(row[index]) for row in rows]
        assert mean(values) == pytest.approx(reference[name + "_mean"]["value"], rel=1e-12)
        assert stdev(values) == pytest.approx(reference[name + "_sample_sd"]["value"], rel=1e-12)
        assert reference[name + "_mean"]["unit"] == "cm"
    assert reference["sepal_length_mean"]["value"] == pytest.approx(5.843333333333334)
    assert reference["petal_length_mean"]["value"] == pytest.approx(3.758)
