-- Makes the current Lua look like Napoleon's: math.huge is nil there.
-- Returns a function that puts the previous value back.
local function napoleon_env()
  local saved_huge = math.huge
  math.huge = nil
  return function()
    math.huge = saved_huge
  end
end

return napoleon_env
