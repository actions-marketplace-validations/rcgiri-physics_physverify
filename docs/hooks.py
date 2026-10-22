"""MkDocs hook: make links that leave docs/ work on the site.

The Markdown files are also read on GitHub, where links such as ../src/..., ../README.md or (in the
changelog) results/... work. Only docs/ is published, so on the site those become links to GitHub.
"""

import re
from pathlib import Path

REPO = "https://github.com/rcgiri-physics/physverify/blob/main/"
ROOT = Path(__file__).resolve().parents[1]
OUTSIDE = re.compile(r"\]\((?:\.\./)+([^)#\s]+)(#[^)\s]*)?\)")
RELATIVE = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)")
FROM_ROOT = {"changelog.md": "CHANGELOG.md", "roadmap.md": "ROADMAP.md"}  # pages that show a top-level file
NOT_PUBLISHED = ("plan_ising.md",)
VERSION = re.search(r'__version__ = "([^"]+)"', (ROOT / "src/physverify/__init__.py").read_text(encoding="utf-8")).group(1)


def on_page_markdown(markdown, page, **kwargs):
    src = page.file.src_uri
    if src in FROM_ROOT:
        text = (ROOT / FROM_ROOT[src]).read_text(encoding="utf-8")
        return RELATIVE.sub(lambda m: f"]({REPO}{m.group(1)})", text)

    if src == "index.md":  # the version on the home page comes from the package, never by hand
        markdown = re.sub(r"\(version \d+\.\d+(?:\.\d+)?\)", f"(version {VERSION})", markdown)

    depth = src.count("/")  # pages in docs/checks/ are one level deeper

    def fix(m):
        if m.group(0)[2:].count("../") <= depth:  # still inside docs/
            return m.group(0)
        return f"]({REPO}{m.group(1)}{m.group(2) or ''})"

    markdown = OUTSIDE.sub(fix, markdown)
    for name in NOT_PUBLISHED:
        markdown = markdown.replace(f"]({name})", f"]({REPO}docs/{name})")
    return markdown
