import asyncio
import json
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def cli(*args, expected=0):
    result = subprocess.run(
        [sys.executable, "-m", "openrepro.cli", *map(str, args)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_cli_workflow(tmp_path):
    root = tmp_path / "exp"
    cli("init", root, "--title", "Study", "--description", "D", "--author", "A", "--json")
    source = tmp_path / "file.txt"
    source.write_text("data")
    cli("add", root, source, "--role", "raw", "--json")
    assert cli("list", tmp_path, "--json")["experiments"][0]["title"] == "Study"
    assert cli("inspect", root, "--json")["metadata"]["files"]
    assert cli("validate", root, "--json")["status"] == "WARN"
    package = tmp_path / "export.orepro"
    cli("export", root, package, "--json")
    cli("import", package, tmp_path / "imported", "--json")
    assert cli("version", "--json")["version"] == "0.1.0"
    (root / "README.md").write_text("tampered")
    assert cli("validate", root, "--json", expected=1)["status"] == "FAIL"
    cli("export", root, tmp_path / "bad.orepro", "--json", expected=2)


def test_real_mcp_stdio(tmp_path):
    async def scenario():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "openrepro.mcp_server", "--workspace", str(tmp_path)],
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                names = {tool.name for tool in (await session.list_tools()).tools}
                assert len(names) == 8

                async def call(name, args):
                    result = await session.call_tool(name, args)
                    assert not result.isError, result
                    return result.structuredContent

                result = await call(
                    "create_experiment",
                    dict(path="exp", title="Study", description="D", authors=["A"]),
                )
                assert result["ok"]
                (tmp_path / "input.csv").write_text("x\n1\n")
                assert (
                    await call(
                        "add_experiment_file", dict(path="exp", source="input.csv", role="raw")
                    )
                )["ok"]
                assert (await call("list_experiments", {}))["result"][0]["title"] == "Study"
                assert (await call("list_experiment_files", {"path": "exp"}))["result"]
                assert (await call("inspect_experiment", {"path": "exp"}))["ok"]
                assert (await call("validate_experiment", {"path": "exp"}))["result"][
                    "status"
                ] == "WARN"
                assert (await call("export_experiment", dict(path="exp", output="study.orepro")))[
                    "ok"
                ]
                assert (
                    await call(
                        "import_experiment", dict(package="study.orepro", destination="imported")
                    )
                )["ok"]
                for path in ("../outside", str(tmp_path / "exp")):
                    assert not (await call("inspect_experiment", {"path": path}))["ok"]
                invalid = await session.call_tool(
                    "add_experiment_file", dict(path="exp", source="input.csv", role="invalid")
                )
                assert invalid.isError

    asyncio.run(asyncio.wait_for(scenario(), timeout=30))
