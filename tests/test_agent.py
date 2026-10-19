"""The assistant hook and the MCP server: a seeded bug in a solver is reported back."""

import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from physverify.agent import find_specs, handle, hook_main, mcp_main

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


@pytest.fixture
def project(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n")
    for name in ("damped_oscillator.py", "verify_damped_oscillator.py"):
        shutil.copy(EXAMPLES / name, tmp_path / name)
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "verify_ignored.py").write_text("raise SystemExit('must not be imported')\n")
    yield tmp_path
    sys.modules.pop("damped_oscillator", None)
    while str(tmp_path) in sys.path:
        sys.path.remove(str(tmp_path))


def seed_bug(project):
    path = project / "damped_oscillator.py"
    path.write_text(path.read_text().replace("damping = 2.0 * GAMMA", "damping = 2.0 * GAMMA * 1.1"))


def event(project, file_name="damped_oscillator.py"):
    return io.StringIO(json.dumps({
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "cwd": str(project),
        "tool_input": {"file_path": str(project / file_name)},
    }))


def test_find_specs_skips_virtual_environments_and_honours_pyproject(project):
    assert [p.name for p in find_specs(project)] == ["verify_damped_oscillator.py"]
    (project / "pyproject.toml").write_text("[tool.physverify]\nspecs = ['verify_damped_oscillator.py']\n")
    assert find_specs(project) == [(project / "verify_damped_oscillator.py").resolve()]


def test_hook_is_silent_on_a_correct_solver(project):
    err = io.StringIO()
    assert hook_main(event(project), err) == 0
    assert err.getvalue() == ""


def test_hook_reports_a_seeded_bug_back_to_the_assistant(project):
    seed_bug(project)
    err = io.StringIO()
    assert hook_main(event(project), err) == 2
    text = err.getvalue()
    assert "checks did not pass" in text and "[mms]" in text and "[patch]" in text


def test_hook_ignores_non_python_edits_and_bad_input(project):
    seed_bug(project)
    assert hook_main(event(project, "notes.md"), io.StringIO()) == 0
    assert hook_main(io.StringIO("not json"), io.StringIO()) == 0


def test_mcp_lists_and_runs_the_tool(project):
    init = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
    assert init["result"]["serverInfo"]["name"] == "physverify"
    assert handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    tools = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
    assert [t["name"] for t in tools] == ["run_checks"]

    seed_bug(project)
    call = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                   "params": {"name": "run_checks", "arguments": {"project": str(project)}}})
    text = call["result"]["content"][0]["text"]
    assert text.startswith("physverify: 4 of 4 checks did not pass")
    report = json.loads(text[text.index("{"):])
    assert report["summary"]["not_ok"] == 4


def test_mcp_errors_are_json_rpc_errors():
    assert handle({"jsonrpc": "2.0", "id": 1, "method": "nope"})["error"]["code"] == -32601
    out = io.StringIO()
    mcp_main(io.StringIO("{bad json\n"), out)
    assert json.loads(out.getvalue())["error"]["code"] == -32700


def test_mcp_server_over_stdio_in_a_subprocess(project):
    """End to end, as a client would run it: python -m physverify mcp."""
    seed_bug(project)
    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "run_checks", "arguments": {"specs": [str(project / "verify_damped_oscillator.py")]}}},
    ]
    proc = subprocess.run(
        [sys.executable, "-m", "physverify", "mcp"],
        input="\n".join(json.dumps(m) for m in lines) + "\n",
        capture_output=True, text=True, timeout=120,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
    )
    responses = [json.loads(l) for l in proc.stdout.splitlines()]
    assert [r["id"] for r in responses] == [1, 2], proc.stderr
    assert "did not pass" in responses[1]["result"]["content"][0]["text"]
