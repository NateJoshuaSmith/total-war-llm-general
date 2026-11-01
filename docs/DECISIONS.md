# Architecture decisions

Newest first.

## 2026-10-31: Lua CI runs stock Lua 5.1 plus a luacheck `napoleon` std

**Decision:** The CI Lua job installs Lua 5.1 and runs `luacheck game/` and `busted tests/lua`. luacheck checks game files against a `napoleon` standard: Lua 5.1 without `math.huge`, plus the game globals the battle script is allowed to use.

**Why:** The game's Lua is missing parts of 5.1 (`math.huge` is nil) and its numbers are single precision. Both of those passed stock Lua on a developer machine and only failed in the game.

**Replaces:** nothing.

## 2026-10-31: Orders file is `key=value` lines ending in `end`

**Decision:** Python and Lua exchange orders through `twllm_orders.txt` in the game root: one `key=value` per line, last line `end`. Keys for Phase 0: `seq`, `unit`, `x`, `z`, `run`. Lua ignores unknown keys, so we can add keys later without breaking old scripts. Python writes it atomically (temp file + rename). The state file `twllm_state.txt` uses the same style.

**Why:** Lua 5.1 has no JSON library and the in-game side has to stay tiny. This format parses with `string.match` and `tonumber`, and the `end` line plus `seq` let Lua ignore half-written, stale and repeated files.

**Replaces:** nothing.

## 2026-10-31: Cursor builds and opens PRs, Claude Code reviews

**Decision:** Each ticket is a GitHub issue. Cursor takes one issue end to end: branch, code, checks, commit, push, open PR. Claude Code reviews the PR and posts a verdict. Nathan merges.

**Why:** The writer shouldn't review its own work, but every handoff between tools is a place to break. The earlier setup (a Cursor stop hook writing a marker file, a Claude Code listener polling for pushes, Nathan pushing by hand) had too many moving parts and only worked while a Claude Code session was open. Now the issue is the brief and the PR is the "done" signal, both of which live on GitHub.

**Replaces:** the Cursor stop hook (`.cursor/hooks.json`) and the push listener.

## 2026-10-31: Layered (n-tier) Python package

**Decision:** All Python lives in one package, `src/tw_general/`, split into layers:

| Layer | Does | May import |
| --- | --- | --- |
| `controllers/` | Entry points (tick loop, viewer routes). Thin: call a service, return. | services, models |
| `services/` | All decisions and logic | repositories, clients, models |
| `repositories/` | Reading and writing files (state, orders, logs) | models |
| `clients/` | Talking to external APIs (Claude) | models |
| `models/` | Pydantic data shapes | nothing in the project |

**Why:** Nathan asked for a controller/service structure. It also fits the testing plan: services take repositories and clients as constructor arguments, so every piece of logic can be tested with fakes, without the game or the Claude API. Keeping file I/O in one layer means a bridge change (Plan A to the log fallback, say) touches only `repositories/`.

**Rules:**
- Imports only go downward. `import-linter` checks this in CI, so a bad import fails the PR.
- No DI framework, abstract base classes or interfaces unless a second implementation actually exists. `main.py` wires things up by hand.
- The Lua side in `game/` stays flat. It is a few hundred lines and has to stay minimal.

**Replaces:** the earlier `bridge/`, `brain/`, `viewer/` top-level folders.
