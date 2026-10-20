"""Run untrusted repositories inside the locked-down container.

    python -I sandbox/sandbox.py build
    python -I sandbox/sandbox.py fetch  <id> <git-url> <commit>   # clone on the host, no hooks, no checkout of LFS
    python -I sandbox/sandbox.py deps   <id> [package ...]        # optional: wheels-only install, network on
    python -I sandbox/sandbox.py run    <id> <script> [args ...]  # network off, repo read-only

Folders (under %LOCALAPPDATA%/physverify-corpus or $PHYSVERIFY_CORPUS):
    repos/<id>   the clone, mounted read-only at /repo
    deps/<id>    extra packages, mounted read-only at /deps during run
    out/<id>     the only writable mount, at /out
The folder holding the script given to `run` is mounted read-only at /work; it is ours (adapters), never the repo's.
"""

import os
import subprocess
import sys
from pathlib import Path

IMAGE = "physverify-sandbox:1"
ROOT = Path(__file__).resolve().parents[1]
CORPUS = Path(os.environ.get("PHYSVERIFY_CORPUS") or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "physverify-corpus")
TIME_LIMIT = int(os.environ.get("PHYSVERIFY_TIME_LIMIT", "900"))  # seconds per run
DEPS_TIME_LIMIT = int(os.environ.get("PHYSVERIFY_DEPS_TIME_LIMIT", "2400"))  # seconds per install (JAX, Qiskit on a slow link)

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


def remove_stale(name):
    """Remove a container left over from an earlier step with the same name.

    A step killed by the host-side time limit can leave its container running; a later install
    into the same deps folder then races it and leaves a half-installed folder.
    """
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)


def timed(args, name, limit):
    try:
        return docker(args, timeout=limit)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", name], capture_output=True)
        print(f"killed after {limit} s")
        return 124


def build():
    return docker(["build", "-t", IMAGE, "-f", str(ROOT / "sandbox" / "Dockerfile"), str(ROOT)])


def fetch(repo_id, url, commit):
    dest = CORPUS / "repos" / repo_id
    if dest.exists():
        sys.exit(f"{dest} exists; delete it first")
    safe = ["-c", "core.hooksPath=/dev/null", "-c", "core.symlinks=false", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.process=",
            "-c", "filter.lfs.clean=", "-c", "filter.lfs.required=false"]  # LFS files stay as small pointer files
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1", GIT_TERMINAL_PROMPT="0")
    subprocess.run(["git", *safe, "clone", "--no-checkout", "--filter=blob:limit=20m", url, str(dest)], check=True, env=env)
    subprocess.run(["git", *safe, "-C", str(dest), "checkout", "--detach", commit], check=True, env=env)
    return 0


def deps(repo_id, packages=()):
    """Install the repo's requirements.txt, or the named packages, into deps/<id>, wheels only, so no setup.py runs.

    The image's own packages are passed as constraints: a dependency that needs a different NumPy fails here
    instead of silently shadowing the image's version during `run`.
    """
    req = CORPUS / "repos" / repo_id / "requirements.txt"
    if packages:
        mounts, what = [], list(packages)
    elif req.exists():
        mounts, what = ["-v", f"{req}:/req.txt:ro"], ["-r", "/req.txt"]
    else:
        print("no requirements.txt and no packages named; nothing to install")
        return 0
    name = f"pv-deps-{repo_id}"
    # pip unpacks wheels in /tmp: give this step more room than a run gets
    lockdown = [a if not a.startswith("--tmpfs=/tmp") else "--tmpfs=/tmp:rw,nosuid,nodev,size=4g" for a in LOCKDOWN]
    # one wheel cache for all repos, so a large package (JAX: 10 minutes) is downloaded once; it holds only
    # wheels from PyPI, and it is mounted in this install step only, never during `run`
    cache = CORPUS / "pip-cache"
    cache.mkdir(parents=True, exist_ok=True)
    remove_stale(name)
    return timed(["run", *lockdown, "--name", name, *mounts, "-v", f"{folder('deps', repo_id)}:/deps:rw",
                  "-v", f"{cache}:/pip-cache:rw", "-e", "PIP_CACHE_DIR=/pip-cache",
                  IMAGE, "pip", "install", "--only-binary=:all:", "--target=/deps",
                  "--constraint=/opt/constraints.txt", *what],
                 name, DEPS_TIME_LIMIT)


def head(repo):
    out = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def host_path(p):
    """A path as Windows Docker needs it: Git-Bash style /c/Users/... becomes C:/Users/..."""
    p = str(p)
    if os.name == "nt" and len(p) > 2 and p[0] == "/" and p[2] == "/" and p[1].isalpha():
        p = f"{p[1].upper()}:{p[2:]}"
    return Path(p).resolve()


def run(repo_id, script, extra):
    script = host_path(script)
    if not script.is_file():
        sys.exit(f"no adapter script at {script}")
    repo = CORPUS / "repos" / repo_id
    if not repo.is_dir():
        sys.exit(f"no clone at {repo}; run fetch first")
    name = f"pv-run-{repo_id}"
    remove_stale(name)
    deps_dir = folder("deps", repo_id)
    # wheels that bundle their own OpenMP runtime (qiskit-aer) fail to load it late ("cannot allocate
    # memory in static TLS block"); preloading it at start-up is the usual fix
    gomp = sorted(deps_dir.glob("*.libs/libgomp*.so*"))
    preload = ["-e", f"LD_PRELOAD=/deps/{gomp[0].relative_to(deps_dir).as_posix()}"] if gomp else []
    args = ["run", *LOCKDOWN, "--network=none", "--name", name, *preload,
            "-v", f"{repo}:/repo:ro", "-v", f"{folder('deps', repo_id)}:/deps:ro",
            "-v", f"{script.parent}:/work:ro", "-v", f"{folder('out', repo_id)}:/out:rw",
            "-e", "PHYSVERIFY_REPO=/repo", *[a for k in os.environ.get("PHYSVERIFY_PASS_ENV", "").split(",") if k for a in ("-e", f"{k}={os.environ[k]}")], "-e", f"PHYSVERIFY_REPO_COMMIT={head(repo)}", IMAGE, "python", f"/work/{script.name}", *extra]
    return timed(args, name, TIME_LIMIT)


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, rest = argv[0], argv[1:]
    if cmd == "build":
        return build()
    if cmd == "fetch" and len(rest) == 3:
        return fetch(*rest)
    if cmd == "deps" and len(rest) >= 1:
        return deps(rest[0], rest[1:])
    if cmd == "run" and len(rest) >= 2:
        return run(rest[0], rest[1], rest[2:])
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
