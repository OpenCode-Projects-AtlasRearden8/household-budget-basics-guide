#!/usr/bin/env python3
"""Tests for the Household Budget Basics guide build.

Run with:  python3 tests.py
Covers the markdown converter, the site build, output integrity
(all links resolve, no double-escaping, worksheets/assets copied), and
the worksheet JavaScript (syntax-checked with node when node exists).
"""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build

ROOT = Path(__file__).resolve().parent


class TestInline(unittest.TestCase):
    def test_escapes_html(self):
        self.assertEqual(build._inline("a & b < c > d"), "a &amp; b &lt; c &gt; d")

    def test_bold(self):
        self.assertEqual(build._inline("**stop buying coffee**"), "<strong>stop buying coffee</strong>")

    def test_italics(self):
        self.assertEqual(build._inline("*actually*"), "<em>actually</em>")

    def test_bold_and_italic(self):
        self.assertEqual(
            build._inline("**good** and *lucky*"),
            "<strong>good</strong> and <em>lucky</em>",
        )

    def test_code_span(self):
        self.assertEqual(build._inline("write the `real` number"), 'write the <code>real</code> number')

    def test_links(self):
        self.assertEqual(
            build._inline("[Start Here](00-start-here.html)"),
            '<a href="00-start-here.html">Start Here</a>',
        )

    def test_links_in_table_cell(self):
        self.assertEqual(
            build._inline("[Sinking Funds](worksheets/sinking-funds.html)"),
            '<a href="worksheets/sinking-funds.html">Sinking Funds</a>',
        )

    def test_amperstand_not_eaten_by_italics(self):
        out = build._inline("Health & pets *and* more")
        self.assertIn("Health &amp; pets", out)
        self.assertIn("<em>and</em>", out)


class TestBlocks(unittest.TestCase):
    def test_headings(self):
        self.assertEqual(build.render_markdown("# One"), "<h1>One</h1>")
        self.assertEqual(build.render_markdown("## Two"), "<h2>Two</h2>")
        self.assertEqual(build.render_markdown("### Three"), "<h3>Three</h3>")
        self.assertEqual(build.render_markdown("#### Four"), "<h4>Four</h4>")

    def test_paragraph(self):
        self.assertEqual(build.render_markdown("hello world"), "<p>hello world</p>")

    def test_paragraph_wraps_lines(self):
        self.assertEqual(build.render_markdown("one\ntwo"), "<p>one two</p>")

    def test_hr(self):
        self.assertEqual(build.render_markdown("---"), "<hr>")

    def test_unordered_list(self):
        self.assertEqual(
            build.render_markdown("- a\n- b"),
            "<ul><li>a</li><li>b</li></ul>",
        )

    def test_ordered_list_with_inline(self):
        self.assertEqual(
            build.render_markdown("1. **first**\n2. second"),
            "<ol><li><strong>first</strong></li><li>second</li></ol>",
        )

    def test_list_continuation_lines(self):
        html = build.render_markdown("- a\n  more a\nb")
        self.assertIn("<ul><li>a more a</li></ul>", html)
        self.assertIn("<p>b</p>", html)

    def test_table(self):
        md = "| A | B |\n| --- | --- |\n| [x](y.html) | 2 |"
        html = build.render_markdown(md)
        self.assertIn("<table><thead><tr><th>A</th><th>B</th></tr></thead>", html)
        self.assertIn('<td><a href="y.html">x</a></td>', html)

    def test_blockquote(self):
        self.assertEqual(
            build.render_markdown('> "bold, together"'),
            '<blockquote><p>"bold, together"</p></blockquote>',
        )

    def test_chapter_headings_with_inline(self):
        self.assertEqual(
            build.render_markdown("## Use it *weekly*"),
            "<h2>Use it <em>weekly</em></h2>",
        )


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hbbg-site-"))
        self.built = build.build(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_all_chapter_pages_built(self):
        slugs = build.slugs_in_order()
        self.assertGreaterEqual(len(slugs), 11)
        for slug in slugs:
            self.assertTrue((self.tmp / f"{slug}.html").exists(), slug)

    def test_index_is_first_chapter(self):
        self.assertEqual(build.slugs_in_order()[0], "index")
        content = (self.tmp / "index.html").read_text(encoding="utf-8")
        self.assertIn("Start Here", content)
        self.assertNotIn("00-start-here.html", content)

    def test_prev_next_wiring(self):
        first = (self.tmp / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="01-paper-first-month.html"', first)
        self.assertNotIn(">e&e&", first)
        second = (self.tmp / "01-paper-first-month.html").read_text(encoding="utf-8")
        self.assertIn('href="index.html"', second)
        self.assertIn('href="02-bills-calendar.html"', second)
        last = (self.tmp / "10-related-guides.html").read_text(encoding="utf-8")
        self.assertIn('href="09-glossary.html"', last)

    def test_all_links_resolve(self):
        self.assertEqual(build.check_links(self.tmp), [])

    def test_worksheets_and_assets_copied(self):
        ws = self.tmp / "worksheets"
        expected = {f.name for f in build.WORKSHEETS_DIR.glob("*.html")}
        for name in expected:
            self.assertTrue((ws / name).exists(), name)
        self.assertTrue((self.tmp / "assets" / "styles.css").exists())
        self.assertTrue((self.tmp / "assets" / "worksheets.js").exists())

    def test_worksheet_links_rewritten_from_docs(self):
        content = (self.tmp / "08-worksheets.html").read_text(encoding="utf-8")
        self.assertIn('href="worksheets/paper-first-month.html"', content)
        self.assertNotIn("../worksheets/", content)

    def test_no_double_escaping(self):
        for file in sorted(self.tmp.rglob("*.html")):
            content = file.read_text(encoding="utf-8")
            self.assertNotIn("&amp;amp;", content, file.name)
            self.assertNotIn("&amp;quot;", content, file.name)

    def test_chapter_pages_have_toc_and_footer(self):
        content = (self.tmp / "05-splurge-line.html").read_text(encoding="utf-8")
        self.assertIn('class="toc"', content)
        self.assertIn('aria-current="page"', content)
        self.assertIn("Asdale Dynamics, LLC", content)
        self.assertIn("MIT licensed", content)

    def test_prev_next_marks_broken_links_on_error(self):
        # A built site with a worksheet removed must report a broken link.
        (self.tmp / "worksheets" / "money-date.html").unlink()
        problems = build.check_links(self.tmp)
        self.assertTrue(any("money-date.html" in p for p in problems))


class TestWorksheetAssets(unittest.TestCase):
    def test_worksheets_reference_shared_css_and_js(self):
        for ws_html in build.WORKSHEETS_DIR.glob("*.html"):
            content = ws_html.read_text(encoding="utf-8")
            self.assertIn('href="../assets/styles.css"', ws_html.name and content)
            self.assertIn('src="../assets/worksheets.js"', content)

    def test_no_external_requests_anywhere(self):
        for html_file in list((ROOT / "docs").rglob("*.md")) + list(build.WORKSHEETS_DIR.glob("*.html")) + list((ROOT / "assets").glob("*")):
            content = html_file.read_text(encoding="utf-8")
            self.assertNotIn("http://", content, html_file.name)
            self.assertNotRegex(content, r"https?://", html_file.name)

    def test_worksheet_js_checked_with_node(self):
        js = ROOT / "assets" / "worksheets.js"
        if shutil.which("node"):
            result = subprocess.run(
                ["node", "--check", str(js)], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_media_outputs_disable_network(self):
        # The worksheet JS must never touch the network (local-first promise).
        js = (ROOT / "assets" / "worksheets.js").read_text(encoding="utf-8")
        self.assertNotIn("fetch(", js)
        self.assertNotIn("XMLHttpRequest", js)


class TestLocalFirstDocs(unittest.TestCase):
    def test_no_secrets_or_keys_in_repo_files(self):
        repo_files = list(Path(ROOT).rglob("*.md")) + list(Path(ROOT).rglob("*.py")) + list(build.WORKSHEETS_DIR.glob("*"))
        # Do not scan this test file: it necessarily contains the patterns themselves.
        repo_files = [f for f in repo_files if f.resolve() != Path(__file__).resolve()]
        for file in repo_files:
            content = file.read_text(encoding="utf-8", errors="ignore").lower()
            for secret in ("api_key", "apikey", "secret_key", "password =", "sk-", "ghp_"):
                self.assertNotIn(secret, content, f"{file.name}: found {secret!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
