# Household Budget Basics

A never-judgy budget manual for real households — plain English, step by step, zero shame. Built as Markdown chapters plus a small static site you can build and read offline.

Written and maintained by **Asdale Dynamics, LLC** (Dylan Asdale's shop for beginner-friendly guides and practical, tested tools).

## What's inside

Eleven chapters, six fill-in worksheets, and a glossary:

| Read | Subject |
| :-- | :-- |
| [docs/00-start-here.md](docs/00-start-here.md) | Who it's for, the one-paragraph version, what it deliberately doesn't cover |
| [docs/01-paper-first-month.md](docs/01-paper-first-month.md) | Spend-on-paper-first month plan |
| [docs/02-bills-calendar.md](docs/02-bills-calendar.md) | One-page bills calendar (30-minute build) |
| [docs/03-sinking-funds.md](docs/03-sinking-funds.md) | Sinking funds for lumpy bills |
| [docs/04-irregular-paychecks.md](docs/04-irregular-paychecks.md) | Paycheck smoothing for shift & variable income |
| [docs/05-splurge-line.md](docs/05-splurge-line.md) | The no-shame splurge line |
| [docs/06-yearly-sweep.md](docs/06-yearly-sweep.md) | Once-a-year insurance & membership sweep |
| [docs/07-money-date.md](docs/07-money-date.md) | The weekly ten-minute money date |
| [docs/08-worksheets.md](docs/08-worksheets.md) | How to use the fill-in worksheets |
| [docs/09-glossary.md](docs/09-glossary.md) | Plain-English glossary |
| [docs/10-related-guides.md](docs/10-related-guides.md) | Companion guides and how they fit together |

Worksheets live in `worksheets/`: they type-in in any browser, save to that browser's local storage only (nothing is ever uploaded), and print cleanly for the fridge.

## Build the static site

```bash
python3 build.py        # builds the site into site/
python3 build.py --out my-folder   # or anywhere else
python3 tests.py        # runs the test suite
```

The build script uses only the Python standard library — no `pip install`, no network, no account. Open `site/index.html` in any browser to read; `python3 -m http.server` in `site/` is optional (plain files work fine).

## Companion guides (different jobs, no repetition)

- **Envelope Budget Webapp** — the digital envelopes tool; this guide explains the *why*, it's the *how*.
- **Subscription Audit Handbook** — the line-by-line subscription deep dive that pairs with the yearly sweep chapter.
- **Credit & Debt Calm Guide** — credit scores, payoff methods, and what to do when payments are behind.

## Repository layout

```text
build.py            stdlib-only static site builder (docs -> site/)
tests.py            test suite for the converter, build, and output
docs/               the manual (Markdown)
worksheets/         fill-in worksheet pages (self-contained HTML)
assets/             one stylesheet + one local-storage worksheet script
site/               generated output (safe to delete; rebuild anytime)
STATUS.md           what was built, verification results, known gaps
```

This guide is education only — not financial, medical, or legal advice.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.
