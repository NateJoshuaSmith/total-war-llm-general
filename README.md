# Total War LLM General

A mod where Claude replaces the battle AI in **Napoleon: Total War**, with **Empire: Total War** to follow. Claude commands the enemy army in real time, and you can toggle its plans on screen.

> **Status: early development (Phase 0).** Nothing is playable yet. We are still confirming what the game's battle scripting allows.

## How it works

Every few seconds:

1. A small Lua script inside the battle writes the state of every unit (position, men alive, ammo, morale) to a file.
2. A Python program on your PC reads that file, builds a short battle report, and asks Claude for orders.
3. Claude picks orders from a fixed menu (move, attack, change formation, and so on). It never writes free-form commands.
4. Python checks every order against the live unit list and drops any bad ones, then writes an orders file.
5. The Lua script carries the orders out.

If Claude is slow or a call fails, units keep their last orders or the game's own AI takes over. The battle never waits on us.

Instant reactions, such as forming square when cavalry charges, run in Lua with no API call.

## Roadmap

| Phase | Goal |
| --- | --- |
| 0 Bridge spike | A Python file makes one unit move in battle |
| 1 Read the battlefield | The Python report matches what's on screen |
| 2 Remote control | Every order in the menu works, sent by hand |
| 3 Claude takes command | Claude finishes a full battle without a crash |
| 4 Make it good | Beats the vanilla AI more often than it loses |
| 5 Port to Empire | The same test battles run in Empire |
| 6 Ship it | Anyone can install it from this README |

## Development setup

Requires Python 3.12 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (on macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
pip install -e .
```

Run the same checks CI runs:

```bash
ruff check .
ruff format --check .
lint-imports
pytest
```

Tests that call the real Claude API are marked `live` and skipped by default. Run them on purpose with `pytest -m live` (needs `ANTHROPIC_API_KEY`, and costs money).

## Project layout

```
src/tw_general/     Python, layered: controllers → services → repositories/clients → models
game/napoleon/      Lua battle script
tests/              pytest suites and recorded game fixtures
docs/DECISIONS.md   Architecture decisions
CLAUDE.md           Full project brief, conventions, and workflow
```

## How we work

Each change starts as a GitHub issue with acceptance criteria. Cursor builds it and opens a PR, Claude Code reviews it, CI must be green, and Nathan merges. See `CLAUDE.md` for the details.

## Disclaimer

Fan project, not affiliated with or endorsed by Creative Assembly or SEGA. You need your own copy of the game. No game files are included in this repo.
