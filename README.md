# MCP Trust Registry

Checks whether an MCP tool's description is honestly describing itself to a
human, or secretly trying to manipulate the AI reading it ("tool
poisoning") — and now keeps a history, so a tool that behaves well at
first and turns malicious in a later version ("a rug pull") gets caught
automatically. Runs entirely for $0 — the AI check uses a local Ollama
model, no API key required.

## How it works

Every scan runs through two independent engines and shows both results
side by side, never blended into one opaque score:

- **Rule-based engine** (`scanner/rules.py`) — plain code, checks for known
  dangerous patterns (hidden-instruction phrasing, credential references,
  fake system tags). Fast, predictable, cannot be fooled by clever wording
  it wasn't written to catch.
- **AI engine** (`scanner/llm_check.py`) — a local model (`qwen2.5:3b` via
  Ollama) reads the description and judges intent semantically, catching
  cases the fixed rules miss. Forced into structured JSON output so the
  result is always machine-parseable.

Every scan result is saved to a local SQLite registry (`scanner/db.py`).
Before saving a new scan, the scanner checks whether this exact
server+tool was ever scanned before — if the grade changed, it's flagged
immediately in the report, not buried in a table you'd have to go look at.

## Run it

Requires Ollama running locally (`ollama serve`) with `qwen2.5:3b` pulled.

```bash
cd scanner
python scan.py ../samples/clean_calculator.json      # expect grade A
python scan.py ../samples/poisoned_calculator.json    # expect grade F
python scan.py ../samples/scope_creep_notes.json      # expect grade F

python history.py                        # leaderboard: every server/tool scanned so far
python history.py notes-sync read_note   # full timeline for one server/tool
```

## The rug-pull scenario (the reason a registry exists at all)

A one-off scan only tells you a tool looks safe *today*. The actual attack
this project cares about is a server that looks clean when it's first
published, earns trust, then quietly changes its behavior later. Reproduce
it:

```bash
cd scanner
python scan.py ../samples/notes_sync_v1_clean.json   # first time seen -> grade A, saved
python scan.py ../samples/scope_creep_notes.json     # same server+tool, later "version" -> grade F
```

The second command's output includes:

```
*** GRADE CHANGED: A -> F (got WORSE) ***
Previous scan was 10s ago.
This is exactly the pattern that catches a "rug pull":
  a server behaving differently than it did last time it was checked.
```

`python history.py notes-sync read_note` then shows the full timeline with
the change point marked.

## What the sample cases prove

| Sample | Rule engine alone | AI engine alone | Combined |
|---|---|---|---|
| `clean_calculator` | 0/100 | low risk | **A** |
| `poisoned_calculator` | 100/100 (obvious keywords) | high risk | **F** |
| `scope_creep_notes` | 25/100 (would read as "B" alone) | high risk (catches the intent) | **F** |
| `notes_sync_v1_clean` → `scope_creep_notes` | — | — | **A → F, flagged automatically** |

The `scope_creep_notes` case is the whole reason this project has two
engines instead of one: the fixed rules only catch one weak signal
("clipboard/browser history" access), but the AI understands *why* an
"analytics sync" bolted onto a simple note-reader is suspicious. Rules
alone would under-grade it. The version-history case is the whole reason
this project is a *registry* instead of a one-shot script.

## Web dashboard

A FastAPI backend (`api/`) exposes the same registry over HTTP, and a
Next.js frontend (`frontend/`) puts a real UI on top of it — a
leaderboard, a per-tool timeline with grade-change markers, and a live
"scan a tool" page anyone can try without touching a terminal.

```bash
# terminal 1 — API (wraps the exact same scanner/db.py the CLI uses)
cd api
pip install -r requirements.txt
python -m uvicorn main:app --port 8001 --reload

# terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. The dashboard, detail pages, and CLI all
read/write the same SQLite registry, so a scan from any of them shows up
everywhere else.

## Next milestones

1. ~~Description scanner (rules + local LLM, CLI)~~ — done
2. ~~Save every scan to a database, detect grade changes over time~~ — done
3. ~~Public web dashboard (Next.js + FastAPI)~~ — done, built ahead of #4 below
4. Run a real MCP server in Docker and compare declared vs. actual behavior — plugs into the same UI once done
5. Deploy live for free, write the full portfolio README
