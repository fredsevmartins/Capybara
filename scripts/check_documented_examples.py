"""Execute the self-contained quick-start and API tutorial in temporary workspaces."""

import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_examples():
    count = 0
    for name in ("docs/quickstart.md", "docs/python-api.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        blocks = re.findall(r"^```(python|bash)\n(.*?)^```", text, re.M | re.S)
        # The API's first block is standalone; subsequent error-handling snippets
        # illustrate responses to deliberately missing workspaces, not a tutorial step.
        if not blocks:
            raise ValueError(f"Missing runnable tutorial: {name}")
        if name.endswith("python-api.md"):
            blocks = blocks[:1]
        with tempfile.TemporaryDirectory(prefix="capybara-docs-") as directory:
            for language, content in blocks:
                if language == "python":
                    commands = [[sys.executable, "-c", content]]
                else:
                    commands = []
                    for line in content.splitlines():
                        if not line.strip() or line.lstrip().startswith("#"):
                            continue
                        arguments = shlex.split(line)
                        if arguments[0] != "openrepro":
                            raise ValueError(f"Unsupported documented command: {line}")
                        commands.append([sys.executable, "-m", "openrepro.cli", *arguments[1:]])
                for command in commands:
                    result = subprocess.run(
                        command, cwd=directory, capture_output=True, text=True, timeout=60
                    )
                    if result.returncode:
                        raise RuntimeError(
                            f"{name}: example failed ({result.returncode})\n"
                            f"{result.stdout}\n{result.stderr}"
                        )
                    count += 1
    print(f"Executed {count} documented tutorial steps in fresh temporary workspaces")


if __name__ == "__main__":
    check_examples()
