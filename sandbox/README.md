# Sandbox for testing other people's code

Every external repository is treated as untrusted. `sandbox.py` runs it in a fresh container with these limits:

| Limit | Setting |
|---|---|
| Network | none (`--network=none`) during `run` |
| File system | root file system read-only; repo mounted read-only at `/repo`; only `/out` and a 512 MB `/tmp` are writable |
| User | uid 10001, all capabilities dropped, `no-new-privileges`, no sudo |
| Resources | 2 CPUs, 2 GB memory (no swap), 256 processes, 1024 open files, 1 GB max file size |
| Time | 900 s per run (`PHYSVERIFY_TIME_LIMIT`), then the container is killed |
| Image | Python 3.12 slim pinned by digest, NumPy, SciPy, SymPy, Matplotlib (Agg), pytest, physverify; libX11 and libGL for wheels that link them |

The repository is cloned on the host with hooks, symlinks and LFS turned off and checked out at a fixed commit. Nothing from the repository runs on the host. Extra requirements, when needed, are installed by `deps` as wheels only (no `setup.py`) into a separate folder that is mounted read-only during `run`; `deps` is the only step with network access.

    python -I sandbox/sandbox.py build
    python -I sandbox/sandbox.py fetch D01 https://github.com/owner/repo <commit>
    python -I sandbox/sandbox.py deps  D01
    python -I sandbox/sandbox.py run   D01 path/to/adapter_script.py

The adapter script's folder is mounted read-only at `/work`, so shared helpers next to it can be imported.

`probe.py` checks the limits from inside; every line should print `OK`. In Git Bash, set `MSYS_NO_PATHCONV=1` so container paths are not rewritten.

## What the adapters taught us

Mistakes made while writing the first adapters, worth avoiding in the next ones:

- Use the code's own constants in the reference. One code used the Gaussian G = 39.4769 au³/(M☉ yr²), not 4π², so a textbook circular orbit was the wrong reference. `physverify.constants.scan` lists such values first.
- Compare at the requested end time, and check the time grid separately (`time_grid_check`). Taking the record nearest `t_end` hid an extra step.
- Before calling a low order a bug, refine. Large-amplitude problems can be pre-asymptotic at the usual step counts, and `check_order` now says when that looks likely.
- A Crank–Nicolson reference with a start that does not match the boundary condition rings; use a few backward Euler steps first (Rannacher start).
- When a sampler fails a statistical check, rerun it with an independently computed observable to tell a sampling bug from a measurement bug.
- Rebuild the image after changing physverify: the image holds a copy of `src/`, not a live mount.
- Taichi fields can be padded to a block size; read only the first N rows.
- With an unshifted pair potential, a pair crossing the cutoff changes the energy by V(r_c) whatever dt is. Choose starting positions with no pair near the cutoff, or the energy check measures the model, not the integrator.
- For Butcher tables, check the order conditions (`physverify.butcher`) before running order studies; they settle the question exactly.
- Corpus data location: set `PHYSVERIFY_CORPUS` (on the author's machine `G:\physverify-corpus`, to keep the C drive free).
