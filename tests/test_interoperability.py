"""RO-Crate conversion is explicit, local, portable and provenance-preserving."""

import json

import pytest

from openrepro.experiments import load
from openrepro.interoperability import convert_crate
from openrepro.models import OpenReproError
from openrepro.validation import validate_experiment


@pytest.fixture
def external_crate(tmp_path):
    source = tmp_path / "external"
    source.mkdir()
    (source / "measurement.csv").write_text("value\n1\n")
    document = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "External study",
                "description": "D",
                "license": "CC-BY-4.0",
                "author": {"@id": "#person"},
                "hasPart": [{"@id": "measurement.csv"}],
            },
            {"@id": "#person", "@type": "Person", "name": "Researcher", "affiliation": "Institute"},
            {"@id": "measurement.csv", "@type": "File", "contentSize": "8"},
            {"@id": "#instrument", "@type": "IndividualProduct", "name": "Extra entity preserved"},
        ],
    }
    (source / "ro-crate-metadata.json").write_text(json.dumps(document))
    return source, document


def test_external_graph_conversion(external_crate, tmp_path):
    source, document = external_crate
    destination = tmp_path / "converted"
    result = convert_crate(source, destination)
    assert result["mapping"]["measurement.csv"] == "measurement.csv"
    assert validate_experiment(destination)["status"] == "PASS"
    assert load(destination).authors == ["Researcher"]
    assert json.loads((destination / "supplementary/source-ro-crate.json").read_text()) == document
    assert (source / "measurement.csv").read_bytes() == (
        destination / "measurement.csv"
    ).read_bytes()


@pytest.mark.parametrize("attack", ["traversal", "remote", "duplicate", "missing", "cycle"])
def test_bad_crate_is_nonmutating(external_crate, tmp_path, attack):
    source, document = external_crate
    if attack in ("traversal", "remote"):
        document["@graph"][0]["hasPart"] = [
            {"@id": "../escape" if attack == "traversal" else "https://example.com/file"}
        ]
        document["@graph"][2]["@id"] = document["@graph"][0]["hasPart"][0]["@id"]
    elif attack == "duplicate":
        document["@graph"].append(document["@graph"][2])
    elif attack == "missing":
        (source / "measurement.csv").unlink()
    else:
        document["@graph"][0]["hasPart"] = [{"@id": "./"}]
    (source / "ro-crate-metadata.json").write_text(json.dumps(document))
    with pytest.raises((OpenReproError, OSError)):
        convert_crate(source, tmp_path / "converted")
    assert not (tmp_path / "converted").exists()


@pytest.mark.parametrize("field,value", [("type", 17), ("type", [17]), ("part", {"@id": []})])
def test_malformed_graph_types_report_input_errors(external_crate, tmp_path, field, value):
    source, document = external_crate
    if field == "type":
        document["@graph"][0]["@type"] = value
    else:
        document["@graph"][0]["hasPart"] = [value]
    (source / "ro-crate-metadata.json").write_text(json.dumps(document))
    with pytest.raises(OpenReproError):
        convert_crate(source, tmp_path / "converted")
    assert not (tmp_path / "converted").exists()
