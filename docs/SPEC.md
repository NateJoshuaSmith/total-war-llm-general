# SPEC: what each piece must do

Phases 0 and 1. Newer phases get added as we reach them. `CLAUDE.md` has the why and the in-game findings; this file says what the code must do. If code and spec disagree, fix one of them in the same PR.

## Game constraints (all phases)

These come from Phase 0 testing in Napoleon (see `CLAUDE.md`, "Phase 0 findings").

- Lua and Python talk **only through files** in the game root (`D:\SteamLibrary\steamapps\common\Napoleon Total War`). Lua opens them with relative paths.
- Our Lua runs as a battle's own script, by overriding `napoleon_historical_battles\<battle>\<battle>_battle.battle_script` from a Mod pack. Only Lodi is set up so far.
- Napoleon's Lua reports 5.1 but **is missing parts of the standard library**: `math.huge` is nil. Use only functions confirmed in game. The script logs a `lua libs:` line at load.
- **Lua numbers are single precision** (about 7 significant digits). Never compare IDs or large numbers as numbers; compare their text.
- Never call `vfs.exists` or touch `package.loaders` (both crash the game, and pcall can't catch it).
- Every Lua entry point the game calls (timer, phase handler) wraps its work in `pcall`. A bad file, a Lua error or a missing unit must never crash or stall the battle.

## Files

| File | Written by | Read by | When |
| --- | --- | --- | --- |
| `twllm_orders.txt` | Python | Lua | Whenever an order is sent |
| `twllm_state.txt` | Lua | Python (Phase 1) | Every tick (3 s) |
| `twllm_bridge_log.txt` | Lua | People | Load, phase changes, orders, errors |

All three are plain ASCII text, one `key=value` per line, `\n` line endings, and **last line `end`**. A reader treats a file without the `end` line as half-written and tries again next tick.

### `twllm_orders.txt`

| Key | Meaning | Rules |
| --- | --- | --- |
| `seq` | Order ID | Positive integer, written as text. Lua acts when the text **differs** from the last one it handled. Python makes it from the clock in ms, always increasing. |
| `unit` | Enemy unit index (1-based) into `alliances():item(2):armies():item(1):units()` | Positive integer, ≤ live unit count (checked in the tick) |
| `action` | `move` or `release` (#20) | Optional; missing means `move` |
| `x`, `z` | Target, meters from map center | Finite numbers; required for `move` |
| `run` | `1` run, `0` walk | Required for `move` |

Unknown keys are ignored. Python writes the file atomically (`.tmp` then rename, retrying if Windows has it locked).

### `twllm_state.txt`

```
tick=12
last_seq=1793507896188
u=2,1,1,536.2,362.8,24
...
end
```

- `tick`: ticks since deploy.
- `last_seq`: the last order ID Lua handled (text, exactly as Python wrote it), or empty.
- One `u=` line per unit: `alliance,army,index,x,z,men_alive`, with x/z to 0.1 m. Phase 1 adds fields (see below). New fields go **on the end** of the line so old readers keep working.

## Phase 0: bridge (done, 2026-10-31)

Gate: a Python file makes one unit move in battle. Passed with #12, #15 and #17.

- **Python `send_order`** (`python -m tw_general.controllers.send_order`): writes one valid order and prints what it sent. Exits with code 2 if the game folder doesn't exist.
- **Lua tick** (every 3 s after `Deployed`): read orders → parse → act only on a new `seq` → check the unit index → take control the first time → `goto_location` → write the state file. An orders file that already exists at deploy is recorded as the baseline and **not** acted on.
- Follow-ups: Lua CI that imitates Napoleon's Lua (#19); release order (#20).

## Phase 1: read the battlefield

Gate: **the report Python builds matches what's on screen**, checked by Nathan pausing a battle and comparing.

### Lua: richer state

Each `u=` line gains, in this order after `men_alive`: `initial_men`, `bearing` (degrees), `type` (`cav`/`inf`/`art`/`other`), `routing` (0/1), `shattered` (0/1), `ammo`. Each read in its own pcall. A field that fails to read is written as empty (`,,`), not dropped, so columns stay in place. No `is_idle` (it doesn't exist in Napoleon).

### Python: state reader

- A repository reads `twllm_state.txt` and returns the raw text, or nothing if the file is missing or has no `end` line.
- A parser turns it into a Pydantic `BattleState`: `tick`, `last_seq`, and a list of `Unit` (alliance, army, index, x, z, men, initial_men, bearing, type, routing, shattered, ammo). A bad `u=` line is skipped and counted, not fatal.
- Which alliance is ours (AI side) vs the enemy (player) is a setting, defaulting to "alliance 2 is ours" for Lodi.

### Python: report builder

A service turns `BattleState` into a short text report for Claude (and people). It must include:
- each of our units: index, type, strength as a % of starting men, position, and status (routing / shattered / ammo low)
- each enemy unit, the same way
- the **nearest enemy** to each of our units, with distance in meters and rough direction (N/NE/E/... using +z as north)
- simple flags: a unit with enemies within 150 m, enemy cavalry within 300 m of our infantry, our units below 50% strength
- army totals for both sides (men now / at start)

The report stays small, aiming for under 2,000 tokens for a 40-unit battle, because Phase 3 sends it every tick.

### Tests and fixtures

- Save real `twllm_state.txt` files from battles into `tests/fixtures/` (at least: start of battle, mid-fight, someone routing).
- Parser tests on those fixtures, plus broken input (no `end`, bad lines, empty fields).
- Report snapshot tests: report built from each fixture matches a saved snapshot.
- Distance and direction math has its own unit tests.
