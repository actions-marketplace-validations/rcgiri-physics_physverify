# Security

## Running other people's code

Most physverify commands **run the code they check**: `physverify run` imports your spec and the solver, `physverify smoke` runs every script, and the hook and MCP server do the same. Only run them on code you trust, or inside the locked-down container described in [sandbox/README.md](sandbox/README.md) (no network, the code mounted read-only, an unprivileged user).

`physverify scan` is the exception: it only reads the source (Python's `ast` module) and never imports or runs it.

## Advisory GCVE-110-VULN-PYPI-2026-000391

Vulnetix first listed this as "dynamic code execution" (CWE-94) in the spec loader. After review they agreed that running the files you point physverify at is the documented purpose, and corrected the record to CWE-829 (CVSS 3.1 7.0, `AV:L/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:H`) for versions 0.1.0 to 0.5.0:

- `physverify hook` took the project root from the folder of the edited file, not from the session folder, and then ran that folder's `verify_*.py`. With the hook enabled, an assistant's edit inside an untrusted folder ran that folder's code.
- The `specs` list in `[tool.physverify]` was not confined to the project root, so an entry such as `../x.py` was run.

**Fixed in 0.5.1:** the hook does nothing for an edit outside the session folder and never looks above it, and `specs` entries that leave the project root are dropped. Tests in `tests/test_agent.py`. If you use the hook, upgrade with `pip install -U physverify`. `physverify run`, `smoke` and the MCP server still run the code you give them, as described above.

Record: https://github.com/Vulnetix/advisory-database/blob/main/vulnetix/VULN-PYPI/2026/0xxx/GCVE-110-VULN-PYPI-2026-000391.json

## Reporting a vulnerability

If you find a way for a checked project to escape the sandbox, or for physverify itself to run code it should not (for example `scan` executing something), please do not open a public issue. Use GitHub's [private vulnerability reporting](https://github.com/rcgiri-physics/physverify/security/advisories/new) or write to rcgiri.physics@gmail.com. You will get an answer within a week. Only the latest release is supported.
