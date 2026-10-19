"""Connect physverify to an AI coding assistant: a Claude Code hook and a minimal MCP server.

Both are thin layers over `physverify.report` (the same code as `physverify run`),
and the core works without them.

Hook (`physverify hook`)
    For Claude Code's PostToolUse event. It reads the event JSON on stdin. After
    an edit to a .py file it runs the project's specs, and when a check fails it
    prints a summary on stderr and exits 2, which Claude Code passes back to the
    assistant. Otherwise it exits 0 and prints nothing. See docs/agent.md.

MCP server (`physverify mcp`)
    Model Context Protocol over stdio (newline-delimited JSON-RPC 2.0), with one
    tool, `run_checks`, that takes spec paths and returns the JSON report. It is
    written with the standard library only, so it has no extra dependency; it
    implements the parts of the protocol a tool server needs (initialize,
    tools/list, tools/call, ping), not the whole specification.

Specs are found in this order: `[tool.physverify] specs = [...]` in the nearest
pyproject.toml, otherwise every verify_*.py under the project folder (skipping
hidden folders, virtual environments and build output).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SKIP_DIRS = {"venv", ".venv", "env", "node_modules", "build", "dist", "__pycache__", "site-packages"}
MAX_REPORTED = 10


def find_project_root(start: Path) -> Path:
    start = start.resolve()
    for folder in [start, *start.parents]:
        if (folder / "pyproject.toml").is_file() or (folder / ".git").exists():
            return folder
    return start


def find_specs(root: Path) -> list[Path]:
    root = Path(root)
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            import tomllib

            config = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("tool", {}).get("physverify", {})
        except Exception:
            config = {}
        if config.get("specs"):
            return [(root / s).resolve() for s in config["specs"]]
    specs = []
    for path in sorted(root.rglob("verify_*.py")):
        parts = path.relative_to(root).parts[:-1]
        if any(p.startswith(".") or p in SKIP_DIRS for p in parts):
            continue
        specs.append(path)
    return specs


def run_specs(specs) -> dict:
    """Run every spec; returns the JSON report as a dict, with load errors listed separately.

    Anything the code under test prints goes to stderr, so that it cannot corrupt
    the MCP stream on stdout.
    """
    import contextlib

    from .report import load_spec, run_checks, to_json

    outcomes, load_errors = [], []
    with contextlib.redirect_stdout(sys.stderr):
        for spec in specs:
            try:
                outcomes += run_checks(load_spec(spec))
            except Exception as exc:
                load_errors.append({"spec": str(spec), "error": f"{type(exc).__name__}: {exc}"})
    report = json.loads(to_json(outcomes, ", ".join(str(s) for s in specs)))
    report["load_errors"] = load_errors
    return report


def failure_summary(report: dict) -> str:
    failed = [c for c in report["checks"] if not c["ok"]]
    lines = [f"physverify: {len(failed)} of {report['summary']['total']} checks did not pass."]
    for c in failed[:MAX_REPORTED]:
        lines.append(f"- {c['status']} [{c['family']}] {c['label']}: {c['message']}")
    if len(failed) > MAX_REPORTED:
        lines.append(f"- ... and {len(failed) - MAX_REPORTED} more")
    for e in report["load_errors"]:
        lines.append(f"- could not load {e['spec']}: {e['error']}")
    lines.append("Run `physverify run <spec> --html report.html` for convergence plots.")
    return "\n".join(lines)


def hook_main(stdin=None, stderr=None) -> int:
    stdin = stdin or sys.stdin
    stderr = stderr or sys.stderr
    try:
        event = json.load(stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # not a hook event; never block the assistant on our own input problem
    tool_input = event.get("tool_input") or {}
    edited = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if edited and not edited.endswith(".py"):
        return 0
    cwd = Path(event.get("cwd") or ".")
    root = find_project_root(Path(edited).parent if edited else cwd)
    specs = find_specs(root)
    if not specs:
        return 0
    report = run_specs(specs)
    if report["summary"]["not_ok"] or report["load_errors"]:
        print(failure_summary(report), file=stderr)
        return 2
    return 0


# --- MCP server ---

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "run_checks",
        "description": (
            "Run physverify verification checks (manufactured solutions, order of convergence, "
            "invariants, limits, exactness) on physics simulation code. Takes spec files that "
            "define checks(); with no specs given, finds verify_*.py files under `project`. "
            "Returns a JSON report: per check family, label, status (PASS, EXACT, FAIL, "
            "INCONCLUSIVE, ERROR), message, observed and expected order, step sizes and errors."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "specs": {"type": "array", "items": {"type": "string"}, "description": "spec file paths"},
                "project": {"type": "string", "description": "project folder to search for verify_*.py"},
            },
        },
    }
]


def handle(message: dict):
    """Answer one JSON-RPC message; returns the response dict, or None for a notification."""
    from . import __version__

    method = message.get("method")
    msg_id = message.get("id")
    if msg_id is None:
        return None  # notifications (initialized, cancelled, ...) need no answer

    def ok(result):
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
        return ok(
            {
                "protocolVersion": requested,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "physverify", "version": __version__},
            }
        )
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        if params.get("name") != "run_checks":
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32602, "message": f"unknown tool {params.get('name')!r}"}}
        args = params.get("arguments") or {}
        specs = [Path(s) for s in args.get("specs") or []]
        if not specs:
            specs = find_specs(Path(args.get("project") or "."))
        if not specs:
            return ok({"content": [{"type": "text", "text": "No spec files found (verify_*.py defining checks())."}], "isError": True})
        report = run_specs(specs)
        failed = bool(report["summary"]["not_ok"] or report["load_errors"])
        text = (failure_summary(report) + "\n\n" if failed else "") + json.dumps(report, indent=2)
        return ok({"content": [{"type": "text", "text": text}], "isError": False})
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"method not found: {method}"}}


def mcp_main(stdin=None, stdout=None) -> int:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            try:
                response = handle(message)
            except Exception as exc:  # keep the server alive; report the failure to the client
                response = {"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32603, "message": f"{type(exc).__name__}: {exc}"}}
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
    return 0
