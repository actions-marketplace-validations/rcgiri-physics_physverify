# Security

## Running other people's code

Most physverify commands **run the code they check**: `physverify run` imports your spec and the solver, `physverify smoke` runs every script, and the hook and MCP server do the same. Only run them on code you trust, or inside the locked-down container described in [sandbox/README.md](sandbox/README.md) (no network, the code mounted read-only, an unprivileged user).

`physverify scan` is the exception: it only reads the source (Python's `ast` module) and never imports or runs it.

## Reporting a vulnerability

If you find a way for a checked project to escape the sandbox, or for physverify itself to run code it should not (for example `scan` executing something), please do not open a public issue. Use GitHub's [private vulnerability reporting](https://github.com/rcgiri-physics/physverify/security/advisories/new) or write to rcgiri.physics@gmail.com. You will get an answer within a week. Only the latest release is supported.
