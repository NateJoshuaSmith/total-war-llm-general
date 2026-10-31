# CLAUDE.md — Total War LLM General

## What this project is

A mod where Claude replaces the battle AI in Napoleon: Total War (first) and Empire: Total War (later). Claude commands the enemy army in real time, and its prompts and plans can be shown on screen with a toggle.

Full roadmap with diagrams (private link, Nathan's): https://claude.ai/artifact/2TSEGW6kKLx91zaepzjVSF

## Roles

- **Nathan**: product owner. Runs the game and in-game tests on his Windows PC, makes product calls, pushes Cursor's branches, merges PRs.
- **Cursor**: implementer. Writes most of the code on feature branches. Its `stop` hook signals when a run is done. It does not open PRs.
- **Claude Code (you)**: senior engineer. You:
  - Turn roadmap phases into small GitHub issues with clear acceptance criteria
  - Watch for Cursor to finish, review its changes, run the tests, and open the PR once Nathan has pushed (see Review workflow)
  - Own architecture decisions and record them in `docs/DECISIONS.md`
  - Keep this file, `docs/SPEC.md`, and the test/CI setup accurate
  - Write small fixes and test scaffolding when asked, but leave feature work to Cursor
  - Push back when a change doesn't match the spec, skips tests, or adds risk. Explain why and suggest the fix.

## Architecture (one tick, every ~3 s)

```
Lua battle script (in game)          Python (on Nathan's PC)              Claude API
reads units on a repeating timer --> state file --> bridge builds report + playbook --> claude-haiku-5-5 / claude-sonnet-5-5
UnitController executes orders  <--  orders file <-- validator drops bad orders  <--  orders JSON (plan + unit orders)
                                                 \-> prompt viewer + log file (every prompt and reply)
```

- Lua and Python only talk through files. Either side can be swapped without touching the other.
- Claude never sends free-form commands. It picks from a fixed order menu, and Python validates every order against a schema and the live unit list before Lua sees it.
- Instant reflexes (e.g. form square when cavalry charges) run in Lua with no API call.
- If a Claude call fails or times out, units keep their last orders or go to the game's AI planner. The battle must never stall or crash because of us.

## Battle scripting API (from CA's Battle Script Documentation)

The docs are Shogun 2 era, so every function must be confirmed in Napoleon during Phase 0.

- Root: `battle = empire_battle:new()`, `battle:alliances():item(n):armies():item(1):units()`
- Unit reads: `position()`, `bearing()`, `number_of_men_alive()`, `initial_number_of_men()`, `is_routing()`, `is_shattered()`, `ammo_left()`, `is_cavalry()`, `is_infantry()`, `is_artillery()`, `is_idle()`, `unit_in_range(u)`, `unit_distance(u)`
- Control: `army:create_unit_controller()`, `add_units`, `take_control`, `release_control`, `goto_location`, `goto_location_angle_width`, `attack_unit(target, primary, fast)`, `attack_location`, `change_formation`, `fire_at_will(bool)`, `skirmish(bool)`, `halt`, `withdraw`
- AI planner (fallback when we're too slow): `alliance:create_ai_unit_planner()`, `defend_position(vec, radius)`, `attack_unit(u)`
- Timing: `register_repeating_timer(name, ms)`, `register_battle_phase_handler(name)` (start the loop on the `Deployed` phase)
- Output: `battle:print()` writes to lua.log; `show_advisor_message(key, text)` / `close_advisor()` for the in-game display
- Reloading: `system.ClearRequiredFiles()` clears cached required files, which enables the log-and-reload bridge fallback
- Positions: `battle_vector(x, y, z)`; x/z are meters from map center, y is height

## Bridge plans

1. **Plan A**: Lua writes a state file and reads an orders file with `io.open`.
2. **Plan A fallback**: Lua prints state to lua.log (Python tails it); Python rewrites a small `orders.lua` that the script reloads each tick.
3. **Plan B**: memory reading via a helper process (WALI-style). Last resort.

Open unknowns that Phase 0 must answer: does battle Lua in Napoleon allow `io`? Can a custom battle load our script? Does `take_control()` exist and do controlled units still fight on their own?

## Phases and gates

We move on when the gate passes, not on a date.

| Phase | Work | Gate |
| --- | --- | --- |
| 0 Bridge spike | Lua reads units, files go in and out | A Python file makes one unit move in battle |
| 1 Read the battlefield | Full state every tick, parsed in Python | Report matches what's on screen |
| 2 Remote control | Hand-written orders, no AI | Every order in the menu works |
| 3 Claude takes command | Prompt loop, validator, prompt viewer | Claude finishes a full battle without a crash |
| 4 Make it good | Playbook, Lua reflexes, test battles | Beats vanilla AI more often than it loses |
| 5 Port to Empire | Same bridge, Empire's function names | Same test battles run in Empire |
| 6 Ship it | Public repo, README, demo video | Anyone can install it from the README |

**Current status:** Phase 0, not started. Repo skeleton is next.

## Decisions made

- Napoleon first, Empire in Phase 5.
- Python 3.12 outside the game, Lua inside. Files are the only interface.
- `claude-haiku-5-5` for the fast loop, `claude-sonnet-5-5` for stronger tactics or a slower plan-setting layer. Haiku 5.5 rejects `temperature` and assistant prefill, so use structured outputs for orders. Keep prompts well under 100K tokens (Haiku's price jumps above that).
- Prompt display has three modes on one hotkey: **Off**, **Plan only** (one-line plan via the in-game advisor window), **Full** (local web viewer). Every prompt and reply is always logged to a file, whatever the mode.
- Tactics come from a short written playbook (`src/tw_general/prompts/playbook.md`) plus real unit stats from the game's data tables, improved from battle logs. No fine-tuning.

## Open decisions (ask Nathan)

- Default display mode at battle start
- Spending cap per battle during testing
- Tick interval (start at 3 s, tune in Phase 3)

## Repo layout

The Python side is layered (n-tier). See `docs/DECISIONS.md` for why.

```
src/tw_general/
  controllers/        Entry points, kept thin: bridge tick loop, viewer HTTP/websocket routes
  services/           All logic: report builder, prompt builder, order validator, cost cap, tick orchestration
  repositories/       File I/O: read state file, write orders file, write prompt/reply log
  clients/            External APIs: Claude client
  models/             Pydantic models: battle state, unit, order, plan
  prompts/            playbook.md and prompt templates
  main.py             Wires the layers together and starts the loop
game/napoleon/        Lua battle script + pack build notes (flat, not layered)
game/empire/          Port, later
eval/                 Test battle list + results log
tests/unit/           pytest, one folder per layer (services/, repositories/, ...)
tests/integration/    Fake game + mocked Claude client, full tick
tests/fixtures/       Recorded state files from real battles
tests/lua/            busted specs for pure Lua functions
scripts/              deploy.ps1 (copy built .pack into the game's data folder)
docs/SPEC.md          What each piece must do
docs/DECISIONS.md     Architecture decisions, newest first
.github/workflows/    CI
.cursor/hooks.json    Cursor stop hook that writes .cursor/agent-done.json
```

## Conventions

- Python: type hints, Pydantic models for state and orders, `ruff` for lint and format.
- Layers only import downward: controllers → services → repositories/clients → models. Models import nothing from the project. `import-linter` enforces this in CI.
- Services get their repositories and clients passed in (constructor arguments), so tests can hand them fakes. No DI framework.
- Lua: keep the in-game side tiny. Wrap every tick in `pcall` so a script error never kills the battle. Log every tick with `battle:print`. Set `luacheck` to the game's Lua version once Phase 0 confirms it.
- Never commit game files, `.pack` files, `.env`, or API keys.
- One ticket per PR, small diffs. Branches: `feat/<issue>-short-name`, `fix/...`.
- No test calls the real Claude API unless it's marked `live`.

## Review workflow

### Cursor done signal

`.cursor/hooks.json` runs `.cursor/hooks/on-stop.ps1` whenever a Cursor agent run ends. The script writes `.cursor/agent-done.json` (gitignored):

```json
{ "status": "completed", "conversation_id": "...", "branch": "feat/3-spec", "head": "<sha>", "dirty": false, "finished_at": "<UTC ISO time>" }
```

`status` is `completed`, `aborted`, or `error`. Only `completed` starts a review.

### Steps

1. Nathan gives Cursor an issue, then asks you to watch for it.
2. Delete any old `.cursor/agent-done.json`, then wait for a new one with the Monitor tool (an until-loop, e.g. `until [ -f .cursor/agent-done.json ]; do sleep 5; done`). You can only listen while a Claude Code session is open. If `status` isn't `completed`, tell Nathan and stop.
3. Review the branch named in the marker against `main`:
   ```
   git diff main...<branch>
   pytest && ruff check . && ruff format --check . && luacheck game/
   ```
   If `dirty` is true, Cursor left uncommitted changes. Review those too and tell Nathan they aren't committed yet.
4. Check whether Nathan has pushed: `git fetch origin`, then compare `git rev-parse <branch>` with `git rev-parse origin/<branch>`.
   - **Not pushed, or the remote is behind:** report the review and test results to Nathan and stop. Never push for him.
   - **Pushed and matching:** open the PR with `gh pr create --base main --head <branch>`, with a title from the issue and a body that starts with `Closes #<issue>`. If the verdict is **Changes requested** or tests fail, open it as `--draft`.
   - Nathan has given standing permission to open PRs for any branch he has pushed, whether or not Cursor wrote it. Don't ask first. Nathan still does all commits, pushes, and merges. When he asks for git steps, give him the commands rather than running them.
5. Post the review with `gh pr review N --comment -b "..."`. Start the comment with a verdict line: **Approve**, **Approve with nits**, or **Changes requested**, and include the test results. Use `--comment` rather than `--approve`, since everything runs under Nathan's GitHub account and GitHub won't let an account approve its own PR.
6. Nathan merges once checks pass and the verdict is Approve.

**Review checklist:**

- Does it do what the issue asked, and only that?
- Does it match `docs/SPEC.md` and the current phase gate?
- Are there tests for new logic, and do they avoid live API calls?
- Can a bad Claude reply, a missing file, or a slow call crash the game or stall the loop?
- Are orders validated before they reach Lua?
- Is the Lua side still minimal and wrapped in `pcall`?
- Any secrets, game files, or `.pack` files in the diff?
- Will the spending cap and logging still work?
- Is anything clever that should be simple?

## Testing strategy

The game can't run in CI, so we test everything around it and record real game output as fixtures.

| Layer | What it covers | Tool | In CI |
| --- | --- | --- | --- |
| Python unit | Order schema, state parser, report builder (flanks, distances), cost cap, display modes | pytest | Yes |
| Prompt snapshots | Prompt built from a fixture state matches the saved snapshot | pytest | Yes |
| Bridge integration | A fake game writes recorded state files, the bridge runs with a mocked Claude client, the orders file is checked | pytest + temp dirs | Yes |
| Lua | Lint, plus pure functions (serialization, order parsing) tested against a stubbed `battle` object | luacheck, busted | Yes |
| Live Claude | Real API on recorded states; every reply must validate | pytest `-m live` | Manual workflow only |
| In-game | Test battles on Nathan's PC, results logged in `eval/` | Manual checklist | No |

From Phase 1 on, save real state files from battles into `tests/fixtures/`. That's how we test against the real game without the game.

## CI/CD plan

- **`ci.yml`**, on every PR and push to `main`, `ubuntu-latest`:
  - Python job: install deps, `ruff check`, `ruff format --check`, `pytest` with coverage
  - Lua job: set up Lua + LuaRocks, `luacheck game/`, `busted tests/lua`
- **`eval.yml`**, manual trigger only (`workflow_dispatch`): runs `pytest -m live` with the `ANTHROPIC_API_KEY` repo secret and a hard spend cap.
- **`release.yml`**, on tags `v*`: zip the Lua scripts and Python bridge and publish a GitHub Release. Build the `.pack` in CI if RPFM's command-line tool works headless; otherwise Nathan builds it locally and attaches it.
- **Local deploy**: `scripts/deploy.ps1` copies the built pack into Napoleon's `data` folder. Never in CI.
- **Branch protection on `main`**: require a PR and passing `ci.yml` checks. Don't require approvals, since it's a single GitHub account.

## First tickets

1. Repo skeleton: folders, `.gitignore`, `requirements.txt`, `pyproject.toml` with ruff and pytest config, placeholder tests, `ci.yml` passing on the empty project. Do this first so every later PR is checked.
2. `.cursor/rules` file that mirrors the conventions and checklist above, so Cursor follows them.
3. `docs/SPEC.md` for Phase 0 and Phase 1.
4. Phase 0 manual checklist for Nathan: install RPFM, open Napoleon's packs, find the historical battle scripts, get a hello-world line into lua.log, test `io.open`, test reloading with `system.ClearRequiredFiles()`.
5. Phase 0 spike: a minimal Lua script that prints unit count and positions on a repeating timer, plus a Python script that reads them and sends one move order back.
