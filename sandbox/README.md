# Sandbox for testing other people's code

Every external repository is treated as untrusted. `sandbox.py` runs it in a fresh container with these limits:

| Limit | Setting |
|---|---|
| Network | none (`--network=none`) during `run` |
| File system | root file system read-only; repo mounted read-only at `/repo`; only `/out` and a 512 MB `/tmp` are writable |
| User | uid 10001, all capabilities dropped, `no-new-privileges`, no sudo |
| Resources | 2 CPUs, 2 GB memory (no swap), 256 processes, 1024 open files, 1 GB max file size |
| Time | 900 s per run (`PHYSVERIFY_TIME_LIMIT`), then the container is killed |
| Image | Python 3.12 slim pinned by digest, NumPy, SciPy, SymPy, Matplotlib (Agg), pytest, physverify |

The repository is cloned on the host with hooks, symlinks and LFS turned off and checked out at a fixed commit. Nothing from the repository runs on the host. Extra requirements, when needed, are installed by `deps` as wheels only (no `setup.py`) into a separate folder that is mounted read-only during `run`; `deps` is the only step with network access.

    python -I sandbox/sandbox.py build
    python -I sandbox/sandbox.py fetch D01 https://github.com/owner/repo <commit>
    python -I sandbox/sandbox.py deps  D01
    python -I sandbox/sandbox.py run   D01 path/to/adapter_script.py

The adapter script's folder is mounted read-only at `/work`, so shared helpers next to it can be imported.

`probe.py` checks the limits from inside; every line should print `OK`. In Git Bash, set `MSYS_NO_PATHCONV=1` so container paths are not rewritten.
