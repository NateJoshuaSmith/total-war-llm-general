-- ===== TWLLM probe 4: can a custom battle reach the battle API? (temporary) =====
-- data/battle_scripted.lua runs in every battle, but before the battle exists
-- (empire_battle was nil there). This probe hooks the game's battle advice
-- events, which fire later in the same battles, and records what each handler
-- can see. Output: twllm_hook_probe.txt in the game root.
--
-- Install: copy to <Napoleon>/data/twllm_hook_probe.lua and add this line at the
-- end of <Napoleon>/data/battle_scripted.lua (back it up first):
--   pcall(require, "data.twllm_hook_probe")
-- Remove: restore the backup and delete twllm_hook_probe.lua.
--
-- Safety: every handler is in pcall and returns false, so advice is unchanged.
-- Only plain Lua and functions confirmed in game. No vfs, no package.loaders,
-- no CliExecute.

local OUT = "twllm_hook_probe.txt"
local MAX_PER_EVENT = 2

local function write_line(text)
  pcall(function()
    local f = io.open(OUT, "a")
    if f then
      f:write(os.date("%H:%M:%S"), " ", tostring(text), "\n")
      f:close()
    end
  end)
end

local function global_names()
  local names = {}
  for k, v in pairs(_G) do
    names[tostring(k)] = type(v)
  end
  return names
end

local function keys_of(t)
  local list = {}
  if type(t) ~= "table" then return "" end
  for k, v in pairs(t) do
    list[#list + 1] = tostring(k) .. "(" .. type(v) .. ")"
  end
  table.sort(list)
  return table.concat(list, " ")
end

local at_load = global_names()
local listed = false

local function report(event_name, context)
  write_line("== " .. event_name)
  write_line("empire_battle=" .. type(empire_battle) .. " battle_vector=" .. type(battle_vector)
    .. " battle=" .. type(battle) .. " twllm_tick=" .. type(twllm_tick)
    .. " conditions=" .. type(conditions) .. " effect=" .. type(effect))

  local added = {}
  for name, kind in pairs(global_names()) do
    if at_load[name] == nil then added[#added + 1] = name .. "(" .. kind .. ")" end
  end
  table.sort(added)
  write_line("globals added since load: " .. table.concat(added, " "))

  write_line("context type=" .. type(context))
  local ok_mt, mt = pcall(getmetatable, context)
  if ok_mt and type(mt) == "table" then
    write_line("context metatable: " .. keys_of(mt))
    if type(mt.__index) == "table" then
      write_line("context methods: " .. keys_of(mt.__index))
    end
  end

  -- Probe 5: what can the advice env read? Lists once, then calls a few
  -- conditions exactly the way CA's export_advice.lua does in the same events.
  if not listed then
    listed = true
    write_line("conditions keys: " .. keys_of(conditions))
    write_line("effect keys: " .. keys_of(effect))
  end
  if ok_mt and type(mt) == "table" then
    write_line("context mt.type=" .. tostring(mt.type))
  end
  local ok_str, context_text = pcall(tostring, context)
  write_line("tostring(context) ok=" .. tostring(ok_str) .. " -> " .. tostring(context_text))
  local calls
  if event_name == "BattleUnitAttacksEnemyUnit" then
    calls = {
      { "BattleUnitIsPlayers" },
      { "BattlePlayerUnitCategory", "cavalry" },
      { "BattlePlayerUnitCategory", "infantry" },
    }
  else
    calls = {
      { "BattleIsLandConflict" },
      { "BattleAllianceIsPlayers" },
      { "BattleAllianceIsAttacker" },
      { "BattleAllianceNumberOfUnits" },
    }
  end
  for _, call in ipairs(calls) do
    local name, arg = call[1], call[2]
    local fn = type(conditions) == "table" and conditions[name]
    if type(fn) == "function" then
      local ok_call, result
      if arg then
        ok_call, result = pcall(fn, arg, context)
      else
        ok_call, result = pcall(fn, context)
      end
      write_line("conditions." .. name .. "(" .. (arg or "") .. ") ok=" .. tostring(ok_call)
        .. " -> " .. tostring(result))
    end
  end

  if type(empire_battle) == "table" or type(empire_battle) == "userdata" then
    local ok_new, bm = pcall(function() return empire_battle:new() end)
    write_line("empire_battle:new() ok=" .. tostring(ok_new) .. " -> " .. tostring(bm))
    if ok_new and bm then
      local ok_count, count = pcall(function() return bm:alliances():count() end)
      write_line("alliances:count() ok=" .. tostring(ok_count) .. " -> " .. tostring(count))
    end
  end
end

local function hook(events, event_name)
  local list = events[event_name]
  if type(list) ~= "table" then
    write_line("no event table " .. event_name)
    return
  end
  local seen = 0
  list[#list + 1] = function(context)
    if seen < MAX_PER_EVENT then
      seen = seen + 1
      pcall(report, event_name, context)
    end
    return false
  end
end

pcall(function()
  write_line("---- probe 5 loaded")
  write_line("events global=" .. type(events) .. " conditions=" .. type(conditions)
    .. " effect=" .. type(effect) .. " CliExecute=" .. type(CliExecute))
  local ok, events_module = pcall(require, "data.events")
  write_line("require data.events ok=" .. tostring(ok) .. " same as global=" .. tostring(events_module == events))
  if not ok or type(events_module) ~= "table" then return end
  hook(events_module, "BattleDeploymentPhaseCommenced")
  hook(events_module, "BattleConflictPhaseCommenced")
  hook(events_module, "BattleUnitAttacksEnemyUnit")
  hook(events_module, "BattleCompleted")
  write_line("hooks added")
end)
