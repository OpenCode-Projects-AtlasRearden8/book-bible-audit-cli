# STATUS.md — book-bible-audit-cli

Last updated: 2026-10-25

## What was built

`bookbible`, a local-first CLI that audits a manuscript draft against a series
bible (CSV or JSON) and writes a Markdown continuity report:

- Bible formats: CSV (flat columns) and JSON (`characters`/`places`), with a
  converter-free schema and sample files for both.
- Entities: characters and places, with canonical names, aliases, eye color,
  title, first-seen/born reference, died reference, status, and free-text notes.
- Audits (all deterministic, sentence-scoped, word-boundary name matching for
  canonical names, aliases, and possessives):
  - eye-color contradictions (e.g., bible green vs. text grey)
  - title contradictions (e.g., bible Professor vs. text Doctor; medium when
    the text uses a title the bible never lists)
  - timeline contradictions (mentions earlier than `first_seen`)
  - dead names: high-severity when a character marked dead is still mentioned
    after their death reference, plus an info-level reminder when any dead
    character still appears (flashback check)
  - unused entities (never mentioned — "ghost" characters and places)
  - repeated phrases (3-grams above a configurable threshold)
  - continuity notes echoed from the bible into the report
- Report: single Markdown file with summary counts, severity-grouped findings
  (each quoting the offending sentence), entity coverage table, repeated
  phrases table, bible notes, and an optional LLM section.
- Optional LLM second opinion via any OpenAI-compatible chat endpoint.
  Default is a **local, keyless Ollama** server (`http://localhost:11434/v1`,
  model `llama3`). Any other base URL/model can be set with flags. An API key
  is optional (flag or `BOOKBIBLE_API_KEY` env var) and is only ever sent as a
  request header — never stored, logged, or written to files.
- Packaging: `pyproject.toml` with a `bookbible` console entry point; zero
  third-party runtime dependencies (Python 3.10+ standard library only).

## How to run it

```bash
# run the audit on the bundled sample
python3 -m bookbible samples/manuscript.md --bible samples/bible.csv -o report.md

# JSON bible instead
python3 -m bookbible samples/manuscript.md --bible samples/bible.json -o report.md

# with the LLM second opinion (requires a running local Ollama, or pass --base-url)
python3 -m bookbible samples/manuscript.md --bible samples/bible.csv --llm -o report.md

# installed console script
pip install .
bookbible --help
```

## Verification results (2026-10-25)

- `python3 -m pytest -q` — **53 passed**, 0 failed (0.1 s).
- `python3 -m bookbible samples/manuscript.md --bible samples/bible.csv` —
  report generated with the canned sample showing all planted issues: 2 eye-
  color contradictions, 1 timeline contradiction, 2 dead-name high findings
  (after-death mentions at Day 6 and Day 7), 1 title mismatch (Doctor vs.
  Professor), 1 unused entity (Ravenreach), 1 repeated phrase ("old lighthouse
  keeper" x4), plus bible notes and coverage table. ✔
- `--bible samples/bible.json` produces the same findings from the JSON bible. ✔
- `--llm` with no server running: the report still saves and the LLM section
  notes that the endpoint was unreachable with guidance to start one. ✔
- LLM call path unit-tested with a mocked HTTP layer (no network in tests),
  covering success, auth header, HTTP error, malformed and empty responses. ✔
- `pip wheel` builds the distribution successfully (stdlib-only). ✔
- No secrets, keys, or personal data anywhere in the repo. ✔

## Known gaps

- Heuristics are intentionally conservative: only "eyes/eye" near a
  character name triggers the eye-color check; long-distance references
  (e.g., "her gaze" several sentences later) are not linked.
- Timeline uses simple `Day N` / `Chapter N` / `in YYYY` references; free-form
  dates ("the winter solstice before Dorian's coronation") are not parsed.
- Flashback detection is not automatic: any dead character who is mentioned
  gets an info-level finding asking the author to confirm intent.
- Repeated-phrase detection is flat 3-grams with a stopword list; very
  intentional stylistic repetition will be flagged too.
- POV attribution and "character X says a line" parsing (quote attribution) is
  not attempted — useful future work for stricter dead-name checking.
- Title matching uses a fixed common-title word list; invented ranks (e.g.,
  "Warden-First") are not recognized.
- The LLM second opinion sends only the first 6,000 characters of the
  manuscript plus a bible summary; it is not a full-book review.
