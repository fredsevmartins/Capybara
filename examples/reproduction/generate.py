"""Create a dependency-free, synthetic end-to-end reproduction demonstration."""

import argparse
import json
from pathlib import Path
from statistics import mean, stdev
from tempfile import TemporaryDirectory

from openrepro.experiments import add_file, create_experiment
from openrepro.models import Role
from openrepro.packages import export_experiment
from openrepro.reproduction import Comparison, Recipe

ANALYSIS = """import csv
import json
from pathlib import Path
from statistics import mean, stdev

with Path("data/raw/observations.csv").open(newline="") as stream:
    values = [float(row["value"]) for row in csv.DictReader(stream)]
summary = {"count": len(values), "mean": mean(values), "sample_sd": stdev(values)}
Path("/output/summary.json").write_text(json.dumps(summary, sort_keys=True) + "\\n")
print("Synthetic analysis complete")
"""


def generate(destination: Path, image: str):
    # Validate before creating anything. The image must already be reviewed and local.
    recipe = Recipe(
        image=image,
        command=["python", "analysis/scripts/analyze.py"],
        comparisons=[
            Comparison(
                reference="results/tables/summary.json", output="summary.json", mode="json-numeric"
            )
        ],
        dependency_files=["supplementary/requirements.txt"],
    )
    destination.mkdir(parents=True, exist_ok=False)
    root = destination / "experiment"
    create_experiment(
        root,
        "SYNTHETIC: descriptive statistics",
        "Four synthetic observations",
        ["OpenRepro demo"],
        reproduction="Review recipe.json, then use openrepro reproduce",
    )
    with TemporaryDirectory() as directory:
        temporary = Path(directory)
        source = temporary / "observations.csv"
        source.write_text("value\n1\n2\n3\n4\n", encoding="utf-8")
        raw = add_file(root, source, Role.raw)
        source = temporary / "analyze.py"
        source.write_text(ANALYSIS, encoding="utf-8")
        script = add_file(root, source, Role.script, derived_from=[raw.path])
        source = temporary / "requirements.txt"
        source.write_text(
            "# Python standard library only; interpreter pinned by image ID\n", encoding="utf-8"
        )
        add_file(root, source, Role.supplementary)
        source = temporary / "summary.json"
        source.write_text(
            json.dumps({"count": 4, "mean": mean([1, 2, 3, 4]), "sample_sd": stdev([1, 2, 3, 4])}),
            encoding="utf-8",
        )
        add_file(root, source, Role.table, derived_from=[raw.path, script.path])
    (destination / "recipe.json").write_text(
        recipe.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    export_experiment(root, destination / "experiment.orepro")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New destination directory")
    parser.add_argument("--image", required=True, help="Reviewed local sha256 image ID")
    args = parser.parse_args()
    print(generate(args.output, args.image))
