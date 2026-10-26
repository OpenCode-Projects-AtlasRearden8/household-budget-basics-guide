#!/usr/bin/env python3
"""Household Budget Basics — site builder.

Converts docs/*.md into a static site in site/ (flat pages + copied
worksheets and assets). Uses only the Python standard library, so the
build runs anywhere Python 3 runs, offline, with no network.

Usage:
    python3 build.py            # build site/ from docs/, worksheets/, assets/
    python3 build.py --out DIR  # build into a different directory
"""

import argparse
import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
WORKSHEETS_DIR = ROOT / "worksheets"
ASSETS_DIR = ROOT / "assets"
DOCS_ORDER = sorted(DOCS_DIR.glob("*.md")) if DOCS_DIR.is_dir() else []

# 00-start-here.md becomes index.html; the rest keep their own slug.
SLUG_OVERRIDES = {"00-start-here": "index"}

SITE_TITLE = "Household Budget Basics"
SITE_SUB = "A never-judgy budget manual for real households"

# ---------------------------------------------------------------------------
# Markdown -> HTML (small, purpose-built for this guide's markdown subset)
# ---------------------------------------------------------------------------


def _inline(text: str) -> str:
    """Render inline markdown: code, bold, italic, links. Input is raw text."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    return text


def _heading_level_and_text(stripped: str):
    m = re.match(r"^(#{1,4})\s+(.+)$", stripped)
    if not m:
        return None
    return len(m.group(1)), m.group(2).strip()


def _is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\|[\s:\-|]+\|$", line.strip()))


def _table_row_to_html(row: str) -> str:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return "".join(f"<td>{_inline(c)}</td>" for c in cells)


def render_markdown(md_text: str) -> str:
    """Convert a constrained markdown subset to an HTML fragment."""
    lines = md_text.splitlines()
    out = []
    i = 0
    n = len(lines)

    while i < n:
        stripped = lines[i].strip()

        if not stripped:
            i += 1
            continue

        heading = _heading_level_and_text(stripped)
        if heading:
            level, text = heading
            out.append(f"<h{level}>{_inline(text)}</h{level}>")
            i += 1
            continue

        if stripped in ("---", "***"):
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            block = []
            while i < n and lines[i].strip().startswith(">"):
                block.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>" + "</p><p>".join(_inline(b) for b in block) + "</p></blockquote>")
            continue

        # A table is a header row, a |---| separator, then body rows.
        if stripped.startswith("|") and i + 1 < n and _is_table_separator(lines[i + 1]):
            header_row = stripped
            i += 2  # skip header and separator
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            thead = "".join(
                f"<th>{_inline(c.strip())}</th>"
                for c in header_row.strip().strip("|").split("|")
            )
            body = "".join(f"<tr>{_table_row_to_html(r)}</tr>" for r in rows)
            out.append(f"<table><thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table>")
            continue

        list_match = re.match(r"^(?:[-*]\s+|\d+[.)]\s+)(.*)$", stripped)
        if list_match:
            ordered = bool(re.match(r"^\d+[.)]\s", stripped))
            tag = "ol" if ordered else "ul"
            items = []
            while i < n:
                s = lines[i].strip()
                m = re.match(r"^(?:[-*]\s+|\d+[.)]\s+)(.*)$", s)
                if m:
                    items.append(m.group(1))
                    i += 1
                elif s and items and lines[i][:1] in (" ", "\t"):
                    items[-1] += " " + s  # indented wrap of the last item
                    i += 1
                else:
                    break
            body = "".join(f"<li>{_inline(itm)}</li>" for itm in items)
            out.append(f"<{tag}>{body}</{tag}>")
            continue

        # Plain paragraph: gather until a blank line.
        block = [stripped]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^(?:#{1,4}\s|[-*]\s|\d+[.)]\s|>|\|)", lines[i].strip()):
            block.append(lines[i].strip())
            i += 1
        out.append("<p>" + f" ".join(_inline(b) for b in block) + "</p>")

    return "\n".join(out)


def rewrite_links(fragment: str) -> str:
    """Map links written relative to docs/ (e.g. ../worksheets/x.html) to site-root paths."""
    fragment = fragment.replace('href="../worksheets/', 'href="worksheets/')
    fragment = fragment.replace('src="../worksheets/', 'src="worksheets/')
    return fragment


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------


def page_title(fragment: str, fallback: str) -> str:
    m = re.search(r"<h1>(.*?)</h1>", fragment, re.S)
    if not m:
        return fallback
    title = re.sub(r"<[^>]+>", "", m.group(1))
    return html.unescape(title).strip() or fallback


def slug_for(doc_path: Path) -> str:
    stem = doc_path.stem
    if stem in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[stem]
    return stem


def slugs_in_order() -> list[str]:
    return [slug_for(d) for d in DOCS_ORDER]


def toc_html(ordered_titles: dict[str, str], current: str) -> str:
    items = []
    for slug in slugs_in_order():
        href = f"{slug}.html"
        current_attr = ' aria-current="page"' if slug == current else ""
        items.append(f'<li><a href="{href}"{current_attr}>{html.escape(ordered_titles[slug])}</a></li>')
    return "\n".join(items)


def wrap_page(fragment: str, ordered_titles: dict[str, str], current: str, prev_slug: str | None,
              next_slug: str | None) -> str:
    title = ordered_titles[current]
    nav = toc_html(ordered_titles, current)

    links = []
    if prev_slug:
        links.append(f'<a href="{prev_slug}.html">&larr; {html.escape(ordered_titles[prev_slug])}</a>')
    if next_slug:
        links.append(f'<a href="{next_slug}.html">{html.escape(ordered_titles[next_slug])} &rarr;</a>')
    prev_next = "\n".join(links)
    if not prev_next:
        prev_next = '<a href="index.html">Start Here</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — {SITE_TITLE}</title>
<meta name="description" content="{SITE_SUB}. Plain-English chapters, fill-in worksheets, zero shame.">
<link rel="stylesheet" href="assets/styles.css">
</head>
<body>
<div class="layout">
<nav class="toc">
  <p class="site-title">{SITE_TITLE}</p>
  <p class="site-sub">{SITE_SUB}</p>
  <ol>
{nav}
  </ol>
</nav>
<main class="chapter">
{fragment}
<div class="prev-next">
{prev_next}
</div>
<div class="site-footer">
<p>Part of the <em>{SITE_TITLE}</em> guide by Asdale Dynamics, LLC. MIT licensed.
Local-first: no accounts, no tracking, no data leaves this page.</p>
</div>
</main>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build(out_dir: Path) -> list[Path]:
    if not DOCS_ORDER:
        raise SystemExit(f"No markdown chapters found in {DOCS_DIR}")

    out_dir.mkdir(parents=True, exist_ok=True)
    ordered_pages = []

    # First pass: titles in order.
    initial_fragments = {}
    for doc in DOCS_ORDER:
        fragment = rewrite_links(render_markdown(doc.read_text(encoding="utf-8")))
        initial_fragments[doc] = fragment
    ordered_titles = {slug_for(d): page_title(initial_fragments[d], d.stem) for d in DOCS_ORDER}

    slugs = slugs_in_order()
    built = []
    for idx, doc in enumerate(DOCS_ORDER):
        slug = slugs[idx]
        fragment = initial_fragments[doc]
        prev_slug = slugs[idx - 1] if idx > 0 else None
        next_slug = slugs[idx + 1] if idx + 1 < len(slugs) else None
        page = wrap_page(fragment, ordered_titles, slug, prev_slug, next_slug)
        dest = out_dir / f"{slug}.html"
        dest.write_text(page, encoding="utf-8")
        built.append(dest)

    # Copy worksheets and assets verbatim.
    if WORKSHEETS_DIR.is_dir():
        ws_out = out_dir / "worksheets"
        ws_out.mkdir(exist_ok=True)
        for f in WORKSHEETS_DIR.glob("*"):
            shutil.copy2(f, ws_out / f.name)
        built.extend(sorted(ws_out.glob("*")))
    if ASSETS_DIR.is_dir():
        as_out = out_dir / "assets"
        as_out.mkdir(exist_ok=True)
        for f in ASSETS_DIR.glob("*"):
            shutil.copy2(f, as_out / f.name)
        built.extend(sorted(as_out.glob("*")))

    return built


def check_links(out_dir: Path) -> list[str]:
    """Every href/src in every built page must exist on disk."""
    problems = []
    for page in sorted(out_dir.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        for href in re.findall(r'(?:href|src)="([^"]+)"', text):
            if href.startswith("http") or href.startswith("#") or href.startswith("javascript:"):
                continue
            target = (page.parent / href.split("#")[0]).resolve()
            if not target.exists():
                problems.append(f"{page.name}: broken link -> {href}")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the Household Budget Basics static site.")
    parser.add_argument("--out", type=Path, default=ROOT / "site", help="output directory (default: site/)")
    args = parser.parse_args(argv)

    built = build(args.out)
    problems = check_links(args.out)
    for p in problems:
        print(f"ERROR: {p}", file=sys.stderr)
    if problems:
        return 1

    pages = [p for p in built if p.suffix == ".html"]
    print(f"Built {len(pages)} HTML pages and {len(built) - len(pages)} other assets into {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
