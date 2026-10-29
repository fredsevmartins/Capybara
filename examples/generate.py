"""Generate fully synthetic experiments; never use these as laboratory evidence.

Run: python examples/generate.py --output examples/generated
"""

import argparse
import csv
import json
import math
import random
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import t

from openrepro.experiments import add_file, create_experiment
from openrepro.models import Role
from openrepro.packages import export_experiment


def pharmacokinetics():
    """One-compartment IV bolus, exact noiseless exponential, mg/L and hours."""
    dose, volume, rate = 100.0, 20.0, 0.2
    times = [i / 4 for i in range(97)]
    concentrations = [dose / volume * math.exp(-rate * x) for x in times]
    auc_observed = sum(
        (b - a) * (c + d) / 2
        for a, b, c, d in zip(times, times[1:], concentrations, concentrations[1:])
    )
    terminal_rate = math.log(concentrations[-2] / concentrations[-1]) / (times[-1] - times[-2])
    auc = auc_observed + concentrations[-1] / terminal_rate
    clearance = dose / auc
    return (
        times,
        concentrations,
        {
            "auc_0_24_mg_h_L": auc_observed,
            "auc_infinity_mg_h_L": auc,
            "terminal_rate_h_inverse": terminal_rate,
            "half_life_h": math.log(2) / terminal_rate,
            "clearance_L_h": clearance,
            "volume_L": clearance / terminal_rate,
            "reference_auc_infinity_mg_h_L": 25.0,
            "reference_clearance_L_h": 4.0,
            "reference_volume_L": 20.0,
            "dose_mg": dose,
        },
    )


def dissolution():
    """Deterministic first-order dissolution, minutes and percent."""
    times = [0, 5, 10, 15, 30, 45, 60]
    percent = [100 * (1 - math.exp(-0.08 * x)) for x in times]
    return (
        times,
        percent,
        {
            "t50_min": math.log(2) / 0.08,
            "t90_min": math.log(10) / 0.08,
            "mean_sampled_percent": sum(percent) / len(percent),
            "final_percent": percent[-1],
        },
    )


def statistics_example():
    """Independent normal synthetic groups; Welch 95% CI, seed 2026."""
    rng = random.Random(2026)
    a = [rng.gauss(10, 2) for _ in range(30)]
    b = [rng.gauss(12, 2) for _ in range(30)]
    mean_a, mean_b = sum(a) / len(a), sum(b) / len(b)
    var_a = sum((x - mean_a) ** 2 for x in a) / (len(a) - 1)
    var_b = sum((x - mean_b) ** 2 for x in b) / (len(b) - 1)
    va, vb = var_a / len(a), var_b / len(b)
    se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1))
    margin = float(t.ppf(0.975, df)) * se
    difference = mean_b - mean_a
    return (
        a,
        b,
        {
            "seed": 2026,
            "n_per_group": 30,
            "mean_a": mean_a,
            "mean_b": mean_b,
            "sd_a": math.sqrt(var_a),
            "sd_b": math.sqrt(var_b),
            "difference_b_minus_a": difference,
            "welch_df": df,
            "ci95_low": difference - margin,
            "ci95_high": difference + margin,
        },
    )


def generate(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    datasets = [
        (
            "pharmacokinetics",
            pharmacokinetics(),
            "time_h",
            "concentration_mg_L",
            "One compartment; IV bolus 100 mg; V=20 L; k=0.2 /h. Noiseless model, no biological "
            "variability. Linear trapezoids to 24 h plus C_last/k tail; terminal log slope. "
            "AUC infinity reference=25 mg h/L, CL=4 L/h, V=20 L; numerical error <0.03%.",
        ),
        (
            "dissolution",
            dissolution(),
            "time_min",
            "dissolved_percent",
            "Synthetic first-order release: 100*(1-exp(-0.08*t)). Assumed sink conditions, "
            "37 degrees C, ideal mixing; these are model assumptions, not measured conditions. "
            "No replicates: no inferential uncertainty. t50=8.664339757 min, t90=28.78231366 min.",
        ),
        (
            "statistics",
            statistics_example(),
            "group_a_arbitrary_units",
            "group_b_arbitrary_units",
            "Seed=2026; 30 independent Gaussian values per group; means 10 and 12, SD=2. "
            "Welch CI for mean B minus mean A using Student-t quantile and Satterthwaite degrees "
            "of freedom. Normal independent observations assumed; no clinical interpretation.",
        ),
    ]
    for name, (x, y, results), x_label, y_label, assumptions in datasets:
        root = output / name
        create_experiment(
            root,
            f"SYNTHETIC: {name}",
            assumptions,
            ["OpenRepro synthetic demo"],
            reproduction="Install openrepro[dev]; run analysis/scripts/generate.py "
            "--output NEW_DIRECTORY from an external directory. Compare results.json.",
        )
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            data = temp / "dataset.csv"
            with data.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow([x_label, y_label])
                writer.writerows(zip(x, y))
            raw = add_file(root, data, Role.raw, "Fully synthetic model values; units in header")
            protocol = temp / "protocol.md"
            protocol.write_text(
                "# SYNTHETIC demonstration\n\n" + assumptions + "\n", encoding="utf-8"
            )
            add_file(root, protocol, Role.protocol)
            add_file(root, Path(__file__), Role.script, "Rebuild all synthetic examples")
            table = temp / "results.json"
            table.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            add_file(root, table, Role.table, "Calculated synthetic results", [raw.path])
            figure, axes = plt.subplots()
            if name == "statistics":
                axes.boxplot([x, y], tick_labels=["A", "B"])
                axes.set_ylabel("Arbitrary units")
            else:
                axes.plot(x, y, "o-")
                axes.set_xlabel(x_label)
                axes.set_ylabel(y_label)
            axes.set_title("SYNTHETIC: " + name)
            figure.tight_layout()
            image = temp / "figure.png"
            figure.savefig(image)
            plt.close(figure)
            add_file(root, image, Role.figure, "Synthetic demonstration plot", [raw.path])
        export_experiment(root, output / f"{name}.orepro")
    return {name: results for name, (_, _, results), *_ in datasets}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("examples/generated"))
    print(json.dumps(generate(parser.parse_args().output), indent=2))
