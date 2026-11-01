"""Expose actual JUnit outcomes in CI summaries without masking the test command."""

import argparse
import html
import os
import xml.etree.ElementTree as ET
from pathlib import Path


def read_report(path: Path) -> dict:
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("JUnit report exceeds 16 MiB")
    root = ET.fromstring(path.read_bytes())
    cases = list(root.iter("testcase"))
    if not cases:
        raise ValueError("No test cases recorded; readiness is not established")
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    failures = []
    for case in cases:
        failure = case.find("failure")
        error = case.find("error")
        skipped = case.find("skipped")
        if failure is not None or error is not None:
            event = failure if failure is not None else error
            counts["failed" if failure is not None else "errors"] += 1
            failures.append(
                {
                    "test": case.get("classname", "") + "::" + case.get("name", ""),
                    "message": " ".join(event.get("message", event.text or "").split())[:1500],
                }
            )
        elif skipped is not None:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
    return {"counts": counts, "failures": failures, "total": len(cases)}


def escape_command(value: str, *, property=False):
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return value.replace(":", "%3A").replace(",", "%2C") if property else value


def summarize(path: Path):
    result = read_report(path)
    counts = result["counts"]
    print("Recorded tests: " + ", ".join(f"{name}={count}" for name, count in counts.items()))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        rows = "".join(
            "<tr><td>"
            + html.escape(item["test"])
            + "</td><td>"
            + html.escape(item["message"])
            + "</td></tr>"
            for item in result["failures"]
        )
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write(
                "## Test outcomes\n\n" + str(result["total"]) + " cases: " + str(counts) + "\n\n"
            )
            if rows:
                stream.write("<table><tr><th>Test</th><th>Failure</th></tr>" + rows + "</table>\n")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for failure in result["failures"]:
            print(
                "::error title="
                + escape_command(failure["test"], property=True)
                + "::"
                + escape_command(failure["message"])
            )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    summarize(parser.parse_args().report)
