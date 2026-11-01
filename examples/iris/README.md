# Attributed Iris reproduction

`iris.csv` is the scikit-learn transcription of 150 historical Iris measurements,
retrieved from an exact Git revision recorded in `source.json`. The original
Fisher/UCI dataset is attributed there, including DOI `10.24432/C56C76` and its
CC-BY-4.0 declaration. That DOI identifies the source dataset, not this generated
OpenRepro experiment. Transcriptions can differ; the source SHA-256 fixes this one.

Four columns contain lengths in centimetres. The analysis uses Python's standard
`statistics` module to calculate arithmetic means and sample standard deviations
with denominator n−1. `reference.json` was calculated separately with NumPy 2.5.4.
Reference generation is independent code, not independent peer review.

```bash
python examples/iris/generate.py --output experiments/iris-demo --image "$REPRO_IMAGE_ID"
openrepro reproduce experiments/iris-demo/experiment --spec experiments/iris-demo/recipe.json --output experiments/iris-run --allow-execution --json
openrepro report experiments/iris-run --output experiments/iris-report.html
```

The recipe checks eight quantities with exact `cm` units, relative tolerance 1e-10
and absolute tolerance 1e-12. This covers floating-point summation differences for
fixed inputs; it is not a claim about biological or instrument uncertainty. The
sample count is checked independently as exact bytes (`150\n`). Species labels
are not analysed. No causal, clinical, classification or generalization claim is made.

The portable tests check fixed reference values, dataset hash and native package
compatibility. Real Docker tests package/import/execute the observations and compare
outputs. Independent researchers and representative new studies are still required
for a stable scientific-product acceptance claim.
