"""Smoke test for the lockdown: every line should say OK."""

import os
import socket
import subprocess

def check(label, ok):
    print(("OK   " if ok else "FAIL ") + label)

try:
    socket.create_connection(("1.1.1.1", 53), timeout=3)
    check("no network", False)
except OSError:
    check("no network", True)
src = "/repo" if os.path.isdir("/repo") else "/repo-src"  # --read-only-repo mounts the clone at /repo
for path in [f"{src}/probe_write", "/usr/probe_write", "/work/probe_write"]:
    try:
        open(path, "w").close()
        check(f"cannot write {path}", False)
    except OSError:
        check(f"cannot write {path}", True)
open("/out/probe_ok", "w").close(); check("can write /out", True)
check("not root", os.getuid() != 0)
check("repo mounted", os.path.isdir(src))
check("PHYSVERIFY_REPO is a folder", os.path.isdir(os.environ.get("PHYSVERIFY_REPO", "")))
try:
    subprocess.run(["sudo", "true"], capture_output=True); check("no sudo", False)
except OSError:
    check("no sudo", True)
import numpy, scipy, physverify
check(f"imports numpy {numpy.__version__}, scipy {scipy.__version__}, physverify", True)
