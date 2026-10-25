# Security

## Running other people's code

Most physverify commands **run the code they check**: `physverify run` imports your spec and the solver, `physverify smoke` runs every script, and the hook and MCP server do the same. Only run them on code you trust, or inside the locked-down container described in [sandbox/README.md](sandbox/README.md) (no network, the code mounted read-only, an unprivileged user).

`physverify scan` is the exception: it only reads the source (Python's `ast` module) and never imports or runs it.

## Advisory GCVE-110-VULN-PYPI-2026-000391

An automated database (Vulnetix) lists "dynamic code execution" (CWE-94) for all physverify versions up to 0.4.2. Its own text says it comes from static analysis, is not a finding of malicious intent, and has not established that untrusted input can reach the flagged call. The calls it refers to are in `physverify.loaders` and the spec loader: running the files you point physverify at is what `physverify run`, `load_definitions_from_path`, `extract_functions` and `load_repaired` are for. physverify never runs code it was not given by you: no code from the network, no code from environment variables, no code from a package's data. The advice above is the remedy: run physverify on code you have not read only inside the sandbox, or use `physverify scan`, which does not execute anything.

## Reporting a vulnerability

If you find a way for a checked project to escape the sandbox, or for physverify itself to run code it should not (for example `scan` executing something), please do not open a public issue. Use GitHub's [private vulnerability reporting](https://github.com/rcgiri-physics/physverify/security/advisories/new) or write to rcgiri.physics@gmail.com. You will get an answer within a week. Only the latest release is supported.
