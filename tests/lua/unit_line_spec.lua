TWLLM_TEST = true
dofile("game/napoleon/lodi_battle.battle_script")

local function returns(value)
  return function()
    return value
  end
end

local function position(x, z)
  return function()
    return {
      get_x = function() return x end,
      get_z = function() return z end,
    }
  end
end

local function full_unit(overrides)
  local unit = {
    position = position(10, -5),
    number_of_men_alive = returns(120),
    initial_number_of_men = returns(160),
    bearing = returns(90),
    is_cavalry = returns(false),
    is_infantry = returns(true),
    is_artillery = returns(false),
    is_routing = returns(false),
    is_shattered = returns(true),
    ammo_left = returns(48),
  }
  if overrides then
    for key, value in pairs(overrides) do
      unit[key] = value
    end
  end
  return unit
end

local function fields_of(line)
  local rest = line:match("^u=(.*)$")
  local fields = {}
  while true do
    local part, tail = rest:match("^(.-),(.*)$")
    if not part then
      fields[#fields + 1] = rest
      break
    end
    fields[#fields + 1] = part
    rest = tail
  end
  return fields
end

describe("twllm_unit_line", function()
  it("writes all 12 fields", function()
    local line = twllm_unit_line(2, 1, 3, full_unit())
    assert.are.equal("u=2,1,3,10.0,-5.0,120,160,90.0,inf,0,1,48", line)
    assert.are.equal(12, #fields_of(line))
  end)

  it("leaves a column empty when a read fails or is nil", function()
    local unit = full_unit({
      is_shattered = function() error("missing") end,
      ammo_left = returns(nil),
    })
    local line = twllm_unit_line(2, 1, 3, unit)
    assert.are.equal("u=2,1,3,10.0,-5.0,120,160,90.0,inf,0,,", line)
    assert.are.equal(12, #fields_of(line))
    assert.are.equal("", fields_of(line)[11])
    assert.are.equal("", fields_of(line)[12])
  end)

  it("writes NaN as an empty column", function()
    local line = twllm_unit_line(2, 1, 3, full_unit({ bearing = returns(0 / 0) }))
    assert.are.equal("u=2,1,3,10.0,-5.0,120,160,,inf,0,1,48", line)
  end)

  it("maps unit type", function()
    local function kind(cav, inf, art)
      local line = twllm_unit_line(1, 1, 1, full_unit({
        is_cavalry = returns(cav),
        is_infantry = returns(inf),
        is_artillery = returns(art),
      }))
      return fields_of(line)[9]
    end
    assert.are.equal("cav", kind(true, false, false))
    assert.are.equal("inf", kind(false, true, false))
    assert.are.equal("art", kind(false, false, true))
    assert.are.equal("other", kind(false, false, false))
  end)
end)
