"""Package the attributed Iris measurements and an independently calculated reference."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from openrepro.experiments import add_file, create_experiment, json_bytes
from openrepro.models import Role
from openrepro.packages import export_experiment
from openrepro.reproduction import Comparison, Recipe


def generate(destination: Path, image: str):
    here = Path(__file__).resolve().parent
    reference_names = ("sepal_length", "sepal_width", "petal_length", "petal_width")
    units = {
        "/" + name + suffix: "cm" for name in reference_names for suffix in ("_mean", "_sample_sd")
    }
    recipe = Recipe(
        image=image,
        command=["python", "analysis/scripts/analyze.py"],
        comparisons=[
            Comparison(
                reference="results/tables/reference.json",
                output="summary.json",
                mode="quantities",
                units=units,
                relative_tolerance=1e-10,
                absolute_tolerance=1e-12,
                justification="Same 150 fixed decimal measurements and n-1 sample SD. "
                "Tolerance covers double-precision summation differences "
                "between NumPy and statistics; "
                "it is not a measurement uncertainty estimate.",
            ),
            Comparison(reference="results/tables/count.txt", output="count.txt", mode="exact"),
        ],
    )
    destination.mkdir(parents=True, exist_ok=False)
    root = destination / "experiment"
    create_experiment(
        root,
        "Iris: descriptive measurements",
        "Descriptive means and sample standard "
        "deviations of the attributed public Iris measurements. "
        "No inference of scientific correctness.",
        ["OpenRepro reproducibility demonstration"],
        license="CC-BY-4.0",
        reproduction="Review protocol and source.json; reproduce using the external recipe.json",
    )
    raw = add_file(
        root,
        here / "iris.csv",
        Role.raw,
        "150 attributed historical observations; measurements in cm",
    )
    script = add_file(
        root, here / "analyze.py", Role.script, "Python statistics implementation", [raw.path]
    )
    add_file(
        root,
        here / "source.json",
        Role.supplementary,
        "Source, attribution, hash and reference method",
    )
    add_file(root, here / "reference.json", Role.table, "Independent NumPy reference", [raw.path])
    with TemporaryDirectory() as directory:
        count = Path(directory) / "count.txt"
        count.write_text("150\n", encoding="utf-8", newline="\n")
        add_file(root, count, Role.table, "Exact sample count", [raw.path])
        protocol = Path(directory) / "protocol.md"
        protocol.write_text(
            "Use all 150 rows. Four length columns are in cm. Compute arithmetic "
            "means and sample standard deviations with denominator n-1. Species labels are unused. "
            "The analysis uses Python statistics; references use NumPy. "
            "See supplementary/source.json for original-data attribution and transcription limits. "
            "No medical or causal claims.\n",
            encoding="utf-8",
        )
        add_file(root, protocol, Role.protocol, derived_from=[script.path])
    (destination / "recipe.json").write_bytes(json_bytes(recipe.model_dump()))
    export_experiment(root, destination / "iris.orepro")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    print(generate(args.output, args.image))
