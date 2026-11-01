-- ===== TWLLM ping test (temporary) =====
-- Append to <Napoleon>/data/battle_scripted.lua, then start any battle.
-- Tries to require twllm_ping.lua, which exists only inside twllm_probe.pack.
-- Pure Lua: no engine calls. Writes twllm_ping_result.txt in the game folder.
pcall(function()
  local out = {}
  -- Control: a file we know lives in data.pack, loaded the same way battle_scripted.lua does.
  local ok_c, err_c = pcall(require, "data.export_advice")
  out[#out + 1] = "control require data.export_advice ok=" .. tostring(ok_c) .. " " .. tostring(err_c)

  local saved_path = package.path
  package.path = package.path .. ";data/?.lua"
  for _, name in ipairs({ "data.twllm_ping", "twllm_ping" }) do
    local ok, err = pcall(require, name)
    out[#out + 1] = "require " .. name .. " ok=" .. tostring(ok) .. " " .. tostring(err)
  end
  package.path = saved_path

  out[#out + 1] = "package.loaders count=" .. tostring(package.loaders and #package.loaders)

  local f = io.open("twllm_ping_result.txt", "w")
  f:write(table.concat(out, "\n"), "\n")
  f:close()
end)
