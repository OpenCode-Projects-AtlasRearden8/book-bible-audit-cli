# bookbible: Book Bible Audit CLI

A local-first author tool that audits a manuscript against your **series bible**
and writes a plain Markdown continuity report. It tracks your characters and
places, flags contradictions (eye color, titles, timeline mentions), surfaces
repeated phrases, warns about dead names kept "on stage," and echoes your bible
notes as continuity reminders.

Built and maintained by **Asdale Dynamics, LLC** — practical, beginner-friendly
tools for writers. See <https://dylanasdale.github.io> for free plain-English AI
guides, including local AI with Ollama.

## Why

Long series drift. Authors forget eye colors, ranks get promoted mid-scene, and
characters who died in book one wander back in through the back door of book
three. This tool reads your bible (a simple spreadsheet or JSON file) and
cross-checks the manuscript draft against it — mostly with boring, reliable
text rules, and optionally with a second opinion from a local LLM.

## Quickstart

```bash
# from this folder
python3 -m bookbible samples/manuscript.md --bible samples/bible.csv -o report.md
```

Or install and use the `bookbible` command:

```bash
pip install .
bookbible samples/manuscript.md --bible samples/bible.json -o report.md
```

Open `report.md` in any Markdown viewer. Sections:

1. **Summary** — counts of high / medium / info findings.
2. **Findings** — contradictions grouped by severity, each quoting the sentence.
3. **Character and place coverage** — mention counts for every bible entry, so
   you can spot "ghost" characters that never appear.
4. **Repeated phrases** — n-grams repeated a threshold number of times.
5. **Continuity notes from the bible** — your own notes echoed back per entity.
6. **Second opinion (LLM)** — optional, see below.

## The bible format

Two formats are supported; pick whichever suits your workflow.

### CSV (spreadsheet-friendly)

Columns: `category,name,aliases,eye_color,title,first_seen,died,status,notes`

- `category`: `character` or `place`
- `name`: canonical name (multi-word names also match on first/last tokens)
- `aliases`: comma-separated nicknames, e.g. `Lena, Vee`
- `eye_color`, `title`: used for contradiction checks
- `first_seen`, `died`: references like `Day 3` or `Chapter 5`
- `status`: `alive` or `dead`
- `notes`: any continuity reminders to echo into the report

See `samples/bible.csv`.

### JSON

```json
{
  "characters": [
    {
      "name": "Elena Vance",
      "aliases": ["Lena"],
      "eye_color": "green",
      "title": "Captain",
      "first_seen": "Day 3",
      "died": "Day 5",
      "status": "dead",
      "notes": "Must not act on-screen after Day 5 except flashback."
    }
  ],
  "places": [{ "name": "Millhaven", "notes": "Home port." }]
}
```

See `samples/bible.json`.

## What gets flagged

| Check | Severity | Example |
|---|---|---|
| Eye color contradiction | high | Bible says green; text says grey |
| Title contradiction | high | Bible says Professor; text says Doctor |
| Timeline contradiction | high | First seen Day 3, text places her at Day 2 |
| Dead name still acting | high | Character died Day 5, text shows her at Day 6 |
| Dead name still mentioned | info | Listed dead, but appears N times (flashbacks?) |
| Title with no bible entry | medium | Text says Sergeant, bible lists no title |
| Unused entity | info | Never mentioned in the manuscript |
| Repeated phrases | list | 3-gram repeated >= threshold times |

All checks are sentence-scoped heuristics with word-boundary name matching
(including aliases and possessives). They are meant to *prompt an author*, not
end the debate.

## CLI options

```text
bookbible MANUSCRIPT --bible BIBLE [-o REPORT.md] [--min-repeat N]
    [--llm] [--base-url URL] [--model NAME] [--api-key KEY] [--timeout S]
```

- `-o` writes the report to a file; without it the report prints to stdout.
- `--min-repeat N` sets the repeated-phrase threshold (default 3).

## Optional LLM second opinion

The report can include a second opinion from any **OpenAI-compatible** chat
endpoint. It is fully optional: the deterministic audit works offline.

```bash
# default: local, keyless Ollama (http://localhost:11434/v1, model llama3)
ollama serve           # in another window, once you have Ollama installed
bookbible draft.md --bible bible.csv --llm -o report.md

# other providers / endpoints: any OpenAI-compatible base URL
bookbible draft.md --bible bible.csv --llm \
  --base-url https://my-endpoint.example/v1 --model my-model
```

- **Keyless by default.** No key is stored, logged, or required.
- If your endpoint does need a key, pass `--api-key` (or set the
  `BOOKBIBLE_API_KEY` environment variable). Keys are only used for the
  `Authorization` header of the request — never written to reports or files.
- If the endpoint is unreachable, the report still saves with a short note in
  the LLM section explaining what to do.

## Privacy

Everything runs locally. The manuscript, bible, and report never leave your
machine unless you point `--base-url` at a remote endpoint yourself. No
telemetry, no accounts, no secrets in any file.

## Development

```bash
python3 -m pytest          # run the test suite
python3 -m bookbible --help
```

Layout:

```text
bookbible/      the package (bible parsing, audits, report, LLM client, CLI)
samples/        sample manuscript + bible in CSV and JSON
tests/          pytest suite with fixtures
```

Python 3.10+ standard library only; no third-party dependencies. Tests use
pytest.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.

A friendly project from Asdale Dynamics, LLC: AI explained "like a friend
would" — plain English, step by step, never condescending.
