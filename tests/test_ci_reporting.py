"""CI reporting must distinguish skips/errors and preserve safe diagnostics."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "ci_report", Path(__file__).resolve().parents[1] / "scripts/summarize_tests.py"
)
reporting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporting)


def test_report_outcomes_and_annotation_escaping(tmp_path, monkeypatch, capsys):
    report = tmp_path / "results.xml"
    report.write_text(
        """<testsuites><testsuite><testcase name="ok"/>
    <testcase name="skipped"><skipped/></testcase>
    <testcase name="failed">
    <failure message="bad&#10;::warning::injection &lt;script&gt;"/></testcase>
    <testcase name="error"><error message="setup error"/></testcase>
    </testsuite></testsuites>""",
        encoding="utf-8",
    )
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    result = reporting.summarize(report)
    assert result["counts"] == {"passed": 1, "failed": 1, "errors": 1, "skipped": 1}
    assert result["total"] == 4
    output = capsys.readouterr().out
    assert len([line for line in output.splitlines() if line.startswith("::error ")]) == 2
    assert not any(line.startswith("::warning") for line in output.splitlines())
    assert "&lt;script&gt;" in summary.read_text()
    assert "<script>" not in summary.read_text()
    assert reporting.escape_command("test,field:part", property=True) == "test%2Cfield%3Apart"


def test_zero_test_report_does_not_establish_success(tmp_path):
    report = tmp_path / "empty.xml"
    report.write_text("<testsuites/>")
    with pytest.raises(ValueError, match="No test cases"):
        reporting.read_report(report)
