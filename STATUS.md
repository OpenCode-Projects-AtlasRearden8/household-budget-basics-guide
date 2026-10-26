# STATUS.md — Household Budget Basics

## What was built

A never-judgy budget manual for real households, delivered as Markdown chapters plus a small static site, tested and committed locally.

- **docs/** — eleven chapters (Markdown):
  - `00-start-here.md` — welcome, who it's for, what the guide deliberately does *not* cover (defers to companion guides)
  - `01-paper-first-month.md` — spend-on-paper-first practice month plan
  - `02-bills-calendar.md` — one-page bills calendar + due-date alignment + annual layer
  - `03-sinking-funds.md` — sinking funds for lumpy bills (funds, lazy math, kind rules)
  - `04-irregular-paychecks.md` — paycheck smoothing (Baseline, Holding Account, surplus order, shift-worker notes)
  - `05-splurge-line.md` — the no-shame splurge line
  - `06-yearly-sweep.md` — yearly insurance/membership sweep checklist (defers audit detail to *Subscription Audit Handbook*)
  - `07-money-date.md` — the weekly ten-minute money date (five steps)
  - `08-worksheets.md` — worksheet index and usage tips
  - `09-glossary.md` — plain-English glossary
  - `10-related-guides.md` — companion guides and a suggested order, without repeating their content
- **worksheets/** — six self-contained fill-in worksheet pages (paper-first month, bills calendar, sinking funds, variable income, yearly sweep, weekly money date). They type-in in any browser, save only to that browser's localStorage, and print cleanly.
- **assets/** — one stylesheet (`styles.css`, shared by site and worksheets) and one small script (`worksheets.js`: localStorage persistence, print/clear buttons, median calculator).
- **build.py** — stdlib-only static site builder: converts `docs/*.md` into `site/` (flat pages with sidebar TOC, prev/next, footer), rewrites worksheet links, copies worksheets + assets, and fails the build on broken links.
- **tests.py** — 32 tests: converter units (inline + blocks), build integration (pages exist, index/prev-next wiring, link resolution, worksheet/link rewriting, no double-escaping, copied files), local-first guarantees (no external requests anywhere, worksheet JS never touches network, node syntax check when node is present), and a repo-wide secret scan.
- **README.md, LICENSE (MIT, exact line `Copyright (c) 2026 Asdale Dynamics, LLC`), .gitignore, this STATUS.md.**
- **site/** — generated output (gitignored; rebuild with `python3 build.py`).

Voice: warm, plain English, "like a friend would," no shame, no moralizing; guided by the Asdale Dynamics, LLC plain-language style. Education only; no financial/medical/legal advice statements included in README.

## How to run it

```bash
python3 build.py            # builds the static site into site/ (stdlib only, offline)
python3 build.py --out DIR  # build somewhere else
python3 tests.py            # run the 32-test suite
```

Read by opening `site/index.html` in any browser. No server, account, internet, or install required. Optional: `python3 -m http.server` inside `site/`.

## Verification results

- `python3 build.py` — succeeds: **17 HTML pages, 2 assets** built into `site/`; broken-link check passes (build exits 1 on any broken link).
- `python3 tests.py` — **32/32 pass, OK** on Python 3.13.
- `node --check assets/worksheets.js` — passes (also verified in the test suite when node exists).
- LICENSE copyright line verified character-exact: `Copyright (c) 2026 Asdale Dynamics, LLC`.
- All internal links in `site/` resolve (link checker runs inside both the build and the tests).
- No external HTTP requests anywhere in docs, worksheets, assets, or generated site; worksheets store data in-browser only.
- Secret scan over all repo files passes (mirrored by a test).
- Problems found and fixed during verification: double-escaped entities in TOC titles; list-continuation parsing; the build's link checker catches removed files (covered by test).

## Known gaps / future work

- The markdown converter implements a purposeful subset (headings, paragraphs, lists with indented continuations, tables, blockquotes, hr, bold/italic/code/links) rather than the full CommonMark spec — nested list structures and nested emphasis are not supported.
- Worksheets save to localStorage keyed per page file; there is no export/multi-page backup beyond printing (a combined "print all" or CSV export could be a follow-up).
- No site search or dark mode; the design intentionally stays print-friendly and dependency-free.
- The companion guides (Envelope Budget Webapp, Subscription Audit Handbook, Credit & Debt Calm Guide) are referenced by name but live as separate projects — links are intentionally prose-only until their repos exist.
- Everything is system-font/serif by design; anyone wanting a webfont would need to break the no-external-requests guarantee.

## Repository notes

- Git initialized and committed with the existing identity; plain commit messages, no Co-authored-by trailers.
- Never pushed, no remotes, nothing published; no secrets or personal data in files (test-enforced).
