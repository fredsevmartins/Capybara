# Synthetic scientific demonstrations

Run `python examples/generate.py --output examples/generated` from the checkout.
Output must not already contain these experiments. Each directory contains the
registered dataset, protocol, complete generator source, results JSON and PNG figure.
Three corresponding `.orepro` archives are exported and re-importable. The generator
requires the `dev` extra; core import/validation does not require plotting libraries.

## Pharmacokinetics

Noiseless one-compartment IV bolus: dose 100 mg, volume 20 L, elimination rate
0.2 h⁻¹. Concentration is `5 exp(-0.2 t)` mg/L at 0.25 h intervals through 24 h.
AUC uses linear trapezoids plus `C_last/k` extrapolation. Terminal rate uses the
last two log concentrations. Half-life is `ln(2)/k`; clearance is dose/AUC and
volume is clearance/k. Exact reference AUC infinity=25 mg·h/L, half-life≈3.465735903 h,
clearance=4 L/h, volume=20 L. Numerical AUC, clearance and volume are within 0.03%
of those references. These calculations assume the specified model and ideal data.

## Dissolution

Ideal first-order dissolution: `100 (1-exp(-0.08 t))` percent, time in minutes.
Assumed sink conditions, ideal mixing and 37 °C are model descriptions, not observations.
t50≈8.664339757 min; t90≈28.782313662 min; final percent at 60 min≈99.177025295.
The arithmetic mean describes sampled time points, not a population inference.
No experimental replicates or uncertainty estimates are fabricated.

## Two-group statistics

Seed 2026 generates 30 independent normal observations per group with theoretical
means 10 and 12 and SD 2 in arbitrary units. Sample SD uses `n-1`. The table reports
sample means, SDs, B−A difference, Welch-Satterthwaite degrees of freedom and a
95% Student-t confidence interval. The CI is checked independently against
`scipy.stats.ttest_ind(..., equal_var=False).confidence_interval()`. Normality and
independence are assumptions; there is no clinical or causal claim.

`tests/test_science.py` checks numerical references, deterministic seeded values,
package export, import and integrity. Expected generated results are captured in
[example-results.json](example-results.json) after running the actual generator.

Prebuilt synthetic archives are in [examples/packages](../examples/packages).
