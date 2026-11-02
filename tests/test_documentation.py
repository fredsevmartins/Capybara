"""Documentation checks tolerate interpreter layout changes, not option drift."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "documentation_reference",
    Path(__file__).resolve().parents[1] / "scripts/documentation_reference.py",
)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def test_usage_wrapping_does_not_change_reference_identity():
    old = "usage: openrepro add --role\n       {raw,protocol}\n       path source\n\noptions:\n  --json\n"
    new = "usage: openrepro add\n       --role {raw,protocol} path source\n\noptions:\n  --json\n"
    assert reference.normalize_help_wrapping(old) == reference.normalize_help_wrapping(new)
    changed = new.replace("{raw,protocol}", "{raw,protocol,script}")
    assert reference.normalize_help_wrapping(old) != reference.normalize_help_wrapping(changed)
    assert reference.normalize_help_wrapping(old) != reference.normalize_help_wrapping(
        new.replace("--json", "--different-option")
    )


def test_signature_uses_public_path_type():
    def accepts_path(value: Path) -> Path:
        return value

    signature = reference.public_signature(accepts_path)
    assert signature == "(value: pathlib.Path) -> pathlib.Path"
