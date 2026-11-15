# Packaging drafts

Files for listings outside PyPI. Only the MCP registry entry is published automatically (see below).

- `conda-forge/recipe.yaml`: a recipe for a pull request to conda-forge/staged-recipes (v1 recipe format).
  Check it with `rattler-build build -r recipe.yaml` first. Update `version` and `sha256` from PyPI for each release.
- `mcp-registry/server.json`: the entry for the MCP registry. `.github/workflows/mcp-registry.yml` publishes it after each
  PyPI release (GitHub OIDC login, no stored token); it can also be run by hand from the Actions tab. By hand on a
  computer: `mcp-publisher login github` then `mcp-publisher publish` in this folder. Set both versions in it to the release.
  The registry checks PyPI ownership by looking for `mcp-name: io.github.rcgiri-physics/physverify` in the README on PyPI,
  so that line has to be in the README of the release named in `version`.
  The MCP server runs the user's code (`docs/agent.md`), which the registry description should not hide.

The GitHub Marketplace listing for `action.yml` is made on the release page: edit a release, tick
"Publish this Action to the GitHub Marketplace" and accept the agreement.
