"""Guided recipe creation, diagnostics and portable HTML reports."""

import html
import json
import platform
import shutil
from pathlib import Path

from .experiments import digest, json_bytes, load, load_json
from .models import OpenReproError, Role
from .reproduction import Comparison, Recipe, _docker, reproduction_plan
from .validation import validate_experiment


def create_recipe(
    root: Path,
    image: str,
    destination: Path,
    *,
    script=None,
    reference=None,
    output=None,
    interpreter="python",
) -> dict:
    manifest = load(root)
    scripts = [item.path for item in manifest.files if item.role == Role.script]
    references = [item.path for item in manifest.files if item.role == Role.table]
    if script is None:
        if len(scripts) != 1:
            raise OpenReproError(
                "Choose --script from registered analysis scripts: " + ", ".join(scripts)
            )
        script = scripts[0]
    if reference is None:
        if len(references) != 1:
            raise OpenReproError(
                "Choose --reference from registered result tables: " + ", ".join(references)
            )
        reference = references[0]
    if script not in scripts or reference not in references:
        raise OpenReproError("Select a registered script and reference table")
    recipe = Recipe(
        image=image,
        command=[interpreter, script],
        comparisons=[
            Comparison(
                reference=reference,
                output=output or Path(reference).name,
                mode="json-numeric" if reference.endswith(".json") else "exact",
            )
        ],
        dependency_files=[
            item.path
            for item in manifest.files
            if Path(item.path).name in {"requirements.lock", "requirements.txt", "uv.lock"}
        ],
    )
    reproduction_plan(root, recipe)
    destination = Path(destination)
    if destination.resolve().is_relative_to(Path(root).resolve()):
        raise OpenReproError("Save the recipe outside the experiment")
    with destination.open("xb") as stream:
        stream.write(json_bytes(recipe.model_dump()))
    return {
        "recipe": str(destination),
        "command": recipe.command,
        "next_step": "Review command, output path and numeric tolerances, then run plan",
        "note": "The analysis must write results under /output",
    }


def doctor(root: Path, *, docker=False) -> dict:
    report = {
        "version": __import__("openrepro").__version__,
        "python": platform.python_version(),
        "platform": platform.system(),
        "experiment": validate_experiment(root),
    }
    if docker:
        if platform.system() != "Linux" or not shutil.which("docker"):
            report["docker"] = {"ready": False, "reason": "Linux and local Docker CLI are required"}
        else:
            try:
                result = json.loads(
                    _docker(
                        "info",
                        "--format",
                        '{"memory":{{json .MemoryLimit}},"swap":{{json .SwapLimit}},'
                        '"pids":{{json .PidsLimit}},"cpu":{{json .CPUCfsQuota}},'
                        '"security":{{json .SecurityOptions}}}',
                    ).stdout
                )
                ready = all(result[key] for key in ("memory", "swap", "pids", "cpu")) and any(
                    item.startswith("name=seccomp") for item in result["security"]
                )
                report["docker"] = {"ready": ready, "capabilities": result}
            except OpenReproError:
                report["docker"] = {
                    "ready": False,
                    "reason": "Local Docker is unavailable or inaccessible",
                }
    report["status"] = (
        "FAIL"
        if report["experiment"]["status"] == "FAIL" or (docker and not report["docker"]["ready"])
        else "PASS"
    )
    return report


def render_report(run: Path, destination: Path) -> dict:
    run, destination = Path(run), Path(destination)
    report_path = run / "report.json"
    report = load_json(report_path)
    status = report.get("status")
    if status not in {"PASS", "FAIL"} or not isinstance(
        report.get("comparison", {}).get("comparisons"), list
    ):
        raise OpenReproError("Invalid run report")

    def esc(value):
        return html.escape(str(value), quote=True)

    rows = []
    for item in report["comparison"]["comparisons"]:
        differences = json.dumps(item.get("differences", []), ensure_ascii=False, indent=2)
        rows.append(
            "<tr><td>"
            + esc(item.get("reference", ""))
            + "</td><td>"
            + esc(item.get("status", ""))
            + "</td><td>"
            + esc(item.get("mode", ""))
            + "</td><td><pre>"
            + esc(differences)
            + "</pre></td></tr>"
        )
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; style-src 'unsafe-inline'\">"
        "<title>OpenRepro run report</title><style>body{font:16px system-ui;max-width:960px;"
        "margin:40px auto;padding:16px}table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #ccc;padding:12px;text-align:left}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere}</style></head><body><h1>Reproduction "
        + status
        + "</h1>"
        "<p>The selected outputs "
        + ("matched" if status == "PASS" else "did not all match")
        + " the references. Scientific validity was not evaluated.</p><dl><dt>Experiment</dt><dd>"
        + esc(report.get("experiment", ""))
        + "</dd><dt>Image</dt><dd>"
        + esc(report.get("image", {}).get("id", ""))
        + "</dd><dt>Exit code</dt><dd>"
        + esc(report.get("exit_code"))
        + "</dd></dl>"
        "<table><thead><tr><th>Reference</th><th>Result</th><th>Comparison</th>"
        "<th>Differences (first 100)</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table><p>Use report.json for the complete machine-readable record.</p>"
        "<p>Source report SHA-256: " + digest(report_path) + "</p></body></html>"
    )
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(document)
    return {"html": str(destination), "status": status, "report_sha256": digest(report_path)}
