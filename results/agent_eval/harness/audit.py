"""List what an agent did outside the rules (docs/plan_agent_eval.md, section 7). Runs no model.

    python -I audit.py SESSION_DIR TRANSCRIPT.jsonl [...]

The rules are in the prompt, not enforced, so each transcript is read after the run: every shell
command that runs a program other than a file reader (ls, cat, sed, grep, ...) and is not a
session.py call, every folder a command names, and every file read or written outside the
repository folder and the session folder are printed. An empty list means no breach was seen.
"""
import json
import re
import sys
from pathlib import Path

CORPUS_REPOS = "g:/physverify-corpus/repos/"
READS = {"ls", "cat", "sed", "head", "tail", "grep", "rg", "find", "wc", "cd", "echo", "pwd", "sort", "uniq",
         "awk", "cut", "tr", "diff", "file", "stat", "du", "nl", "less", "more", "true", "pip"}
PATH = re.compile(r"(?:[a-zA-Z]:|/[a-z])/[^\s;'\"|&]+")


def norm(p):
    return str(p).replace("\\", "/").lower()


def audit(sdir, transcript):
    s = json.loads((Path(sdir) / "session.json").read_text(encoding="utf-8"))
    allowed = (norm(Path(sdir).resolve()), CORPUS_REPOS + s["repo_id"].lower(), "prompt2_", "prompt_",
               "physverify/results/agent_eval/harness/session.py", "python314/python")
    found = []
    for ln in open(transcript, encoding="utf-8"):
        try:
            content = json.loads(ln).get("message", {}).get("content") or []
        except (json.JSONDecodeError, AttributeError):
            continue
        for c in content:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            i = c["input"]
            cmd = i.get("command", "")
            # heredoc bodies are file contents, and quoted text is arguments: neither is a command
            bare = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\s*$", "<<HEREDOC", cmd, flags=re.S | re.M)
            bare = re.sub(r"'[^']*'|\"[^\"]*\"", "Q", bare)
            for part in re.split(r"&&|;|\|\|?|\n", bare):
                words = part.split()
                if not words or "session.py" in part:
                    continue
                prog = words[0].rsplit("/", 1)[-1].lower()
                if prog not in READS or prog == "pip" and "install" in words:
                    found.append(f"runs code outside the sandbox: {part.strip()[:160]}")
            for p in PATH.findall(cmd):
                q = norm(re.sub(r"^/([a-z])/", r"\1:/", p))
                if q.startswith(("c:/", "g:/")) and not any(a in q for a in allowed):
                    found.append(f"shell touches another folder: {p}")
            for key in ("file_path", "path", "notebook_path"):
                if i.get(key) and not any(a in norm(i[key]) for a in allowed):
                    found.append(f"{c['name']} outside allowed folders: {i[key]}")
    return found


if __name__ == "__main__":
    sdir, *ts = sys.argv[1:]
    for t in ts:
        print(t, "->", audit(sdir, t) or "no breach seen")
