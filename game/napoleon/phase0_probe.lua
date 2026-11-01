-- ===== TWLLM Phase 0 probe (temporary) =====
-- Paste at the END of <Napoleon>/data/battle_scripted.lua, then start any battle.
-- Reports what this Lua environment allows. Everything is in pcall, so it can't break the battle.
-- To remove: restore battle_scripted.lua.twllm-backup.
pcall(function()
  local out = {}
  local function note(s)
    out[#out + 1] = tostring(s)
    pcall(print, "TWLLM " .. tostring(s))
  end

  note("probe ran, os.date=" .. tostring(os and os.date and os.date() or "n/a"))
  note("lua version: " .. tostring(_VERSION))
  note("io=" .. tostring(io) .. " os=" .. tostring(os) .. " require=" .. tostring(require)
    .. " package=" .. tostring(package))
  note("package.path=" .. tostring(package and package.path))
  note("empire_battle=" .. tostring(empire_battle) .. " system=" .. tostring(system))
  note("system.ClearRequiredFiles=" .. tostring(system and system.ClearRequiredFiles))

  local ok_b, bm = pcall(function() return empire_battle:new() end)
  note("empire_battle:new() ok=" .. tostring(ok_b) .. " -> " .. tostring(bm))
  if ok_b and bm then
    pcall(function() bm:print("TWLLM hello from battle_scripted.lua") end)
    note("register_repeating_timer=" .. tostring(bm.register_repeating_timer))
    note("alliances=" .. tostring(bm.alliances))
  end

  local names = {}
  for k, v in pairs(_G) do names[#names + 1] = tostring(k) .. " (" .. type(v) .. ")" end
  table.sort(names)
  note("globals: " .. table.concat(names, ", "))

  local function write_to(path)
    local ok, result = pcall(function()
      local f = assert(io.open(path, "w"))
      f:write(table.concat(out, "\n"), "\n")
      f:close()
      local r = assert(io.open(path, "r"))
      local first = r:read("*l")
      r:close()
      return first
    end)
    note("write+read " .. path .. " ok=" .. tostring(ok) .. " -> " .. tostring(result))
  end

  write_to("twllm_probe.txt")
  local tmp = os and os.getenv and os.getenv("TEMP")
  if tmp then write_to(tmp .. "\\twllm_probe.txt") end
end)
