# MCP Trust Registry — Milestone 1: Description Scanner

Checks a single MCP tool's description for signs it's trying to manipulate
the AI reading it ("tool poisoning") rather than honestly describing itself
to a human. Runs entirely for $0 — the AI check uses a local Ollama model,
no API key required.

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

## Run it

```bash
cd scanner
python scan.py ../samples/clean_calculator.json      # expect grade A
python scan.py ../samples/poisoned_calculator.json    # expect grade F
python scan.py ../samples/scope_creep_notes.json      # expect grade F
```

Requires Ollama running locally (`ollama serve`) with `qwen2.5:3b` pulled.

## What the three sample cases prove

| Sample | Rule engine alone | AI engine alone | Combined |
|---|---|---|---|
| `clean_calculator` | 0/100 | low risk | **A** |
| `poisoned_calculator` | 100/100 (obvious keywords) | high risk | **F** |
| `scope_creep_notes` | 25/100 (would read as "B" alone) | high risk (catches the intent) | **F** |

The third case is the whole reason this project has two engines instead of
one: the fixed rules only catch one weak signal ("clipboard/browser
history" access), but the AI understands *why* an "analytics sync" bolted
onto a simple note-reader is suspicious. Rules alone would under-grade it.

## Next milestones

1. ~~Description scanner (rules + local LLM, CLI)~~ — done
2. Save every scan to a database, build scan history per server
3. Run a real MCP server in Docker and compare declared vs. actual behavior
4. Public web dashboard (Next.js)
5. Deploy live for free, write the full portfolio README
