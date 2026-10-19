"""Run untrusted repositories inside the locked-down container.

    python -I sandbox/sandbox.py build
    python -I sandbox/sandbox.py fetch  <id> <git-url> <commit>   # clone on the host, no hooks, no checkout of LFS
    python -I sandbox/sandbox.py deps   <id>                      # optional: wheels-only install, network on
    python -I sandbox/sandbox.py run    <id> <script> [args ...]  # network off, repo read-only

Folders (under %LOCALAPPDATA%/physverify-corpus or $PHYSVERIFY_CORPUS):
    repos/<id>   the clone, mounted read-only at /repo
    deps/<id>    extra packages, mounted read-only at /deps during run
    out/<id>     the only writable mount, at /out
The script given to `run` is mounted read-only at /work/<name>; it is ours (an adapter), never the repo's.
"""

import os
import subprocess
import sys
from pathlib import Path

IMAGE = "physverify-sandbox:1"
ROOT = Path(__file__).resolve().parents[1]
CORPUS = Path(os.environ.get("PHYSVERIFY_CORPUS") or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "physverify-corpus")
TIME_LIMIT = int(os.environ.get("PHYSVERIFY_TIME_LIMIT", "900"))  # seconds per run

LOCKDOWN = [
    "--rm",
    "--read-only",
    "--cap-drop=ALL",
    "--security-opt=no-new-privileges",
    "--pids-limit=256",
    "--memory=2g",
    "--memory-swap=2g",
    "--cpus=2",
    "--ulimit=nofile=1024:1024",
    "--ulimit=fsize=1073741824",  # no file over 1 GB
    "--tmpfs=/tmp:rw,nosuid,nodev,size=512m",
    "--user=10001:10001",
    "--env=OMP_NUM_THREADS=2",
]


def folder(kind, repo_id):
    path = CORPUS / kind / repo_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def docker(args, timeout=None):
    print("+ docker " + " ".join(args), flush=True)
    return subprocess.run(["docker", *args], timeout=timeout).returncode


def build():
    return docker(["build", "-t", IMAGE, "-f", str(ROOT / "sandbox" / "Dockerfile"), str(ROOT)])


def fetch(repo_id, url, commit):
    dest = CORPUS / "repos" / repo_id
    if dest.exists():
        sys.exit(f"{dest} exists; delete it first")
    safe = ["-c", "core.hooksPath=/dev/null", "-c", "core.symlinks=false", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.process="]
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1", GIT_TERMINAL_PROMPT="0")
    subprocess.run(["git", *safe, "clone", "--no-checkout", "--filter=blob:limit=20m", url, str(dest)], check=True, env=env)
    subprocess.run(["git", *safe, "-C", str(dest), "checkout", "--detach", commit], check=True, env=env)
    return 0


def deps(repo_id):
    """Install the repo's requirements.txt into deps/<id>, wheels only, so no setup.py runs."""
    req = CORPUS / "repos" / repo_id / "requirements.txt"
    if not req.exists():
        print("no requirements.txt; nothing to install")
        return 0
    name = f"pv-deps-{repo_id}"
    return docker(["run", *LOCKDOWN, "--name", name,
                   "-v", f"{req}:/req.txt:ro", "-v", f"{folder('deps', repo_id)}:/deps:rw",
                   IMAGE, "pip", "install", "--no-cache-dir", "--only-binary=:all:", "--target=/deps", "-r", "/req.txt"],
                  timeout=TIME_LIMIT)


def run(repo_id, script, extra):
    script = Path(script).resolve()
    repo = CORPUS / "repos" / repo_id
    if not repo.is_dir():
        sys.exit(f"no clone at {repo}; run fetch first")
    name = f"pv-run-{repo_id}"
    args = ["run", *LOCKDOWN, "--network=none", "--name", name,
            "-v", f"{repo}:/repo:ro", "-v", f"{folder('deps', repo_id)}:/deps:ro",
            "-v", f"{script}:/work/{script.name}:ro", "-v", f"{folder('out', repo_id)}:/out:rw",
            "-e", "PHYSVERIFY_REPO=/repo", IMAGE, "python", f"/work/{script.name}", *extra]
    try:
        return docker(args, timeout=TIME_LIMIT)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", name], capture_output=True)
        print(f"killed after {TIME_LIMIT} s")
        return 124


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, rest = argv[0], argv[1:]
    if cmd == "build":
        return build()
    if cmd == "fetch" and len(rest) == 3:
        return fetch(*rest)
    if cmd == "deps" and len(rest) == 1:
        return deps(*rest)
    if cmd == "run" and len(rest) >= 2:
        return run(rest[0], rest[1], rest[2:])
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
