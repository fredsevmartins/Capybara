"""Descriptive measurements only; no classification or causal claims."""

import csv
import json
from pathlib import Path
from statistics import mean, stdev

with Path("data/raw/iris.csv").open(newline="", encoding="utf-8") as stream:
    rows = list(csv.reader(stream))[1:]
columns = ("sepal_length", "sepal_width", "petal_length", "petal_width")
result = {}
for index, name in enumerate(columns):
    values = [float(row[index]) for row in rows]
    result[name + "_mean"] = {"value": mean(values), "unit": "cm"}
    result[name + "_sample_sd"] = {"value": stdev(values), "unit": "cm"}
Path("/output/summary.json").write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
Path("/output/count.txt").write_text(str(len(rows)) + "\n", encoding="utf-8")
