"""Explicit end-to-end acceptance against the package installed in this interpreter.

Downloads one binary dependency and runs reviewed Docker analysis. No public
research publication is performed. Use a new output directory.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import openrepro


def accept(destination: Path, image: str):
    checkout = Path(__file__).resolve().parents[1]
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)

    def cli(*arguments):
        command = [sys.executable, "-m", "openrepro.cli", *map(str, arguments), "--json"]
        completed = subprocess.run(
            command, cwd=destination, check=True, capture_output=True, text=True
        )
        return json.loads(completed.stdout)

    example = destination / "iris"
    subprocess.run(
        [
            sys.executable,
            str(checkout / "examples/iris/generate.py"),
            "--output",
            str(example),
            "--image",
            image,
        ],
        cwd=destination,
        check=True,
        capture_output=True,
    )
    root = example / "experiment"
    assert cli("doctor", root, "--docker")["status"] == "PASS"
    guided = destination / "guided-recipe.json"
    cli(
        "recipe",
        root,
        "--image",
        image,
        "--output",
        guided,
        "--reference",
        "results/tables/reference.json",
    )
    requirements = destination / "requirements.in"
    requirements.write_text("six==1.17.0\n", encoding="utf-8")
    cli("add", root, requirements, "--role", "supplementary")
    resolved = destination / "environment"
    cli(
        "environment-lock",
        root,
        "--requirements",
        "supplementary/requirements.in",
        "--base-image",
        image,
        "--output",
        resolved,
        "--allow-download",
    )
    spec = json.loads((example / "recipe.json").read_text())
    spec["command"] = [
        "python",
        "-c",
        "import six,runpy; assert six.__version__=='1.17.0'; "
        "runpy.run_path('analysis/scripts/analyze.py',run_name='__main__')",
    ]
    recipe = destination / "recipe.json"
    recipe.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    cli("plan", root, "--spec", recipe)
    run = destination / "run"
    report = cli(
        "reproduce",
        root,
        "--spec",
        recipe,
        "--environment",
        resolved / "environment.json",
        "--allow-build",
        "--output",
        run,
        "--allow-execution",
    )
    assert report["status"] == "PASS"
    assert report["environment_build"]["image"] == report["image"]["id"]
    assert cli("compare", root, "--spec", recipe, "--outputs", run / "outputs")["status"] == "PASS"
    html = destination / "iris-report.html"
    cli("report", run, "--output", html)
    package = destination / "iris-reproducible.orepro"
    cli("export", root, package)
    catalog = destination / "catalog"
    record = cli("publish", package, "--catalog", catalog)
    assert cli("search", catalog, "--query", "Iris")["packages"]
    received = destination / "received"
    cli("fetch", catalog, record["sha256"], received)
    assert cli("validate", received)["status"] == "PASS"
    csl = cli("cite", catalog, record["sha256"])
    (destination / "citation.csl.json").write_text(
        json.dumps(csl, indent=2) + "\n", encoding="utf-8"
    )
    bundle = destination / "zenodo-bundle"
    deposit = cli("deposit-bundle", package, "--output", bundle)
    assert deposit["doi"] is None and deposit["status"] == "LOCAL_ONLY"
    schemas = destination / "schemas"
    schemas.mkdir()
    for kind in ("manifest", "recipe", "environment"):
        cli("schema", "--kind", kind, "--output", schemas / (kind + ".json"))
    external = destination / "external-crate"
    external.mkdir()
    (external / "measurement.csv").write_text("value\n1\n", encoding="utf-8")
    crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "Acceptance conversion",
                "description": "Test fixture",
                "author": [{"@id": "#author"}],
                "license": "CC-BY-4.0",
                "hasPart": [{"@id": "measurement.csv"}],
            },
            {"@id": "#author", "@type": "Person", "name": "OpenRepro acceptance fixture"},
            {"@id": "measurement.csv", "@type": "File", "contentSize": "8"},
        ],
    }
    (external / "ro-crate-metadata.json").write_text(json.dumps(crate), encoding="utf-8")
    converted = destination / "converted"
    cli("convert-crate", external, "--output", converted)
    assert cli("validate", converted)["status"] == "PASS"
    summary = {
        "status": "PASS",
        "version": openrepro.__version__,
        "installed_module": openrepro.__file__,
        "html_report": str(html),
        "package": str(package),
        "catalog_identifier": record["identifier"],
        "environment_image": report["image"]["id"],
        "numeric_comparisons": len(report["comparison"]["comparisons"]),
        "live_zenodo": "NOT_RUN",
        "pypi_publication": "NOT_RUN",
        "independent_user_acceptance": "NOT_RUN",
    }
    (destination / "acceptance.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--allow-execution", action="store_true")
    args = parser.parse_args()
    if not args.allow_download or not args.allow_execution:
        parser.error(
            "This acceptance case requires both explicit --allow-download and --allow-execution"
        )
    print(json.dumps(accept(args.output, args.image), indent=2))
