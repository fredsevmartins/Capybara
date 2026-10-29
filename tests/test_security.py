import stat
import zipfile

import pytest

from openrepro.experiments import add_file, bounded, create_experiment
from openrepro.models import OpenReproError, Role, safe_path
from openrepro.packages import export_experiment, import_experiment
from openrepro.validation import validate_experiment


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/tmp/escape",
        "C:/escape",
        "a\\b",
        "a/../b",
        "a//b",
        "./x",
        "CON.txt",
        "x.",
        "x ",
        "a\x00b",
        "a:b",
    ],
)
def test_unsafe_paths(name):
    with pytest.raises(OpenReproError):
        safe_path(name)


@pytest.mark.parametrize(
    "attack",
    [
        "traversal",
        "absolute",
        "symlink",
        "duplicate",
        "case",
        "ratio",
        "count",
        "size",
        "conflict",
        "directory",
    ],
)
def test_malicious_zip(tmp_path, monkeypatch, attack):
    from openrepro import packages

    package = tmp_path / "bad.orepro"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if attack == "symlink":
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "../outside")
        elif attack in ("duplicate", "case"):
            archive.writestr("file", "x")
            with (
                pytest.warns(UserWarning)
                if attack == "duplicate"
                else __import__("contextlib").nullcontext()
            ):
                archive.writestr("file" if attack == "duplicate" else "FILE", "y")
        elif attack == "ratio":
            archive.writestr("bomb", b"0" * 100000)
        elif attack == "count":
            monkeypatch.setattr(packages, "MAX_FILES", 1)
            archive.writestr("a", "x")
            archive.writestr("b", "y")
        elif attack == "size":
            monkeypatch.setattr(packages, "MAX_FILE", 1)
            archive.writestr("a", "too big")
        elif attack == "conflict":
            archive.writestr("a", "x")
            archive.writestr("a/b", "y")
        else:
            archive.writestr(
                {"traversal": "../escape", "absolute": "/escape", "directory": "a/"}[attack], "x"
            )
    with pytest.raises(OpenReproError):
        import_experiment(package, tmp_path / "imported")
    assert package.exists()
    assert not (tmp_path / "imported").exists()
    assert not list(tmp_path.glob(".openrepro-import-*"))


def test_malformed_zip(tmp_path):
    package = tmp_path / "broken"
    package.write_bytes(b"not zip")
    with pytest.raises(OpenReproError):
        import_experiment(package, tmp_path / "dest")


def test_tampered_package(tmp_path):
    root = tmp_path / "root"
    create_experiment(root, "T", "D", ["A"])
    good = export_experiment(root, tmp_path / "good.orepro")
    bad = tmp_path / "bad.orepro"
    with zipfile.ZipFile(good) as source, zipfile.ZipFile(bad, "w") as target:
        for info in source.infolist():
            target.writestr(
                info, b"tampered" if info.filename == "README.md" else source.read(info)
            )
    with pytest.raises(OpenReproError):
        import_experiment(bad, tmp_path / "dest")


def test_symlinks_and_workspace_boundary(tmp_path):
    root = tmp_path / "root"
    create_experiment(root, "T", "D", ["A"])
    source = tmp_path / "source"
    source.write_text("secret")
    link = root / "link"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Symlink creation unavailable")
    with pytest.raises(OpenReproError):
        bounded(root, "link")
    with pytest.raises(OpenReproError):
        add_file(root, link, Role.raw)
    assert validate_experiment(root)["status"] == "FAIL"
    with pytest.raises(OpenReproError):
        bounded(root, "../source")


@pytest.mark.parametrize(
    "attack",
    [
        "missing_metadata",
        "unsafe_manifest",
        "oversize_metadata",
        "unsupported_schema",
        "invalid_json",
    ],
)
def test_bad_package_metadata(tmp_path, attack):
    import json

    from openrepro.experiments import load

    root = tmp_path / "root"
    create_experiment(root, "T", "D", ["A"])
    package = tmp_path / "bad.orepro"
    data = load(root).model_dump(mode="json")
    if attack == "unsafe_manifest":
        data["files"][0]["path"] = "../outside"
    if attack == "unsupported_schema":
        data["schema_version"] = "2"
    with zipfile.ZipFile(package, "w") as archive:
        for path in root.rglob("*"):
            if path.is_file():
                name = path.relative_to(root).as_posix()
                content = path.read_bytes()
                if name == "manifest.json":
                    if attack == "missing_metadata":
                        continue
                    content = json.dumps(data).encode()
                    if attack == "invalid_json":
                        content = b"{broken"
                    if attack == "oversize_metadata":
                        content = b" " * (4 * 1024 * 1024 + 1)
                archive.writestr(name, content)
    with pytest.raises(OpenReproError):
        import_experiment(package, tmp_path / "dest")
    assert not (tmp_path / "dest").exists()
