TWLLM_TEST = true
dofile("game/napoleon/lodi_battle.battle_script")

local function read_fixture()
  local handle = assert(io.open("tests/fixtures/orders_example.txt", "rb"))
  local text = handle:read("*a")
  handle:close()
  return text
end

local function as_lf(text)
  return text:gsub("\r\n", "\n"):gsub("\r", "\n")
end

local function drop_key(text, key)
  local kept = {}
  for line in (as_lf(text) .. "\n"):gmatch("(.-)\n") do
    if line ~= "" and not line:match("^" .. key .. "=") then
      kept[#kept + 1] = line
    end
  end
  return table.concat(kept, "\n") .. "\n"
end

local function replace_value(text, key, value)
  local kept = {}
  for line in (as_lf(text) .. "\n"):gmatch("(.-)\n") do
    if line:match("^" .. key .. "=") then
      kept[#kept + 1] = key .. "=" .. value
    elseif line ~= "" then
      kept[#kept + 1] = line
    end
  end
  return table.concat(kept, "\n") .. "\n"
end

local function insert_before_end(text, extra)
  local normalized = as_lf(text)
  if not normalized:match("\n$") then
    normalized = normalized .. "\n"
  end
  local updated = normalized:gsub("end\n$", extra .. "\nend\n")
  return updated
end

local function assert_rejected(text)
  local order, reason = twllm_parse_orders(text)
  assert.is_nil(order)
  assert.is_not_nil(reason)
  return reason
end

local fixture = read_fixture()

describe("twllm_parse_orders", function()
  it("parses the fixture", function()
    local order, reason = twllm_parse_orders(fixture)
    assert.is_nil(reason)
    assert.are.equal(1730400000000, order.seq)
    assert.are.equal("1730400000000", order.seq_text)
    assert.are.equal(1, order.unit)
    assert.are.equal(536.0, order.x)
    assert.are.equal(363.0, order.z)
    assert.is_true(order.run)
  end)

  it("parses CRLF line endings", function()
    local order, reason = twllm_parse_orders(as_lf(fixture):gsub("\n", "\r\n"))
    assert.is_nil(reason)
    assert.are.equal(1, order.unit)
    assert.is_true(order.run)
  end)

  it("ignores an unknown key", function()
    local order, reason = twllm_parse_orders(insert_before_end(fixture, "foo=bar"))
    assert.is_nil(reason)
    assert.are.equal(1730400000000, order.seq)
    assert.are.equal(536.0, order.x)
    assert.is_true(order.run)
  end)

  it("rejects an empty string", function()
    assert.are.equal("no end line", assert_rejected(""))
  end)

  it("rejects nil", function()
    assert_rejected(nil)
  end)

  it("rejects a missing end line", function()
    local without_end = as_lf(fixture):gsub("\nend\n$", "\n")
    assert.are.equal("no end line", assert_rejected(without_end))
  end)

  it("rejects a missing seq", function()
    assert_rejected(drop_key(fixture, "seq"))
  end)

  it("rejects a missing unit", function()
    assert_rejected(drop_key(fixture, "unit"))
  end)

  it("rejects a missing x", function()
    assert_rejected(drop_key(fixture, "x"))
  end)

  it("rejects a missing z", function()
    assert_rejected(drop_key(fixture, "z"))
  end)

  it("rejects a missing run", function()
    assert_rejected(drop_key(fixture, "run"))
  end)

  it("rejects x=abc", function()
    assert_rejected(replace_value(fixture, "x", "abc"))
  end)

  it("rejects x=nan", function()
    assert_rejected(replace_value(fixture, "x", "nan"))
  end)

  it("rejects x=inf", function()
    assert_rejected(replace_value(fixture, "x", "inf"))
  end)

  it("rejects unit=0", function()
    assert_rejected(replace_value(fixture, "unit", "0"))
  end)

  it("rejects unit=1.5", function()
    assert_rejected(replace_value(fixture, "unit", "1.5"))
  end)

  it("rejects seq=-3", function()
    assert_rejected(replace_value(fixture, "seq", "-3"))
  end)

  it("rejects run=2", function()
    assert_rejected(replace_value(fixture, "run", "2"))
  end)

  it("rejects a line with no equals sign", function()
    assert_rejected(insert_before_end(fixture, "hello"))
  end)

  it("keeps seq text that a short float would round together", function()
    local function with_seq(seq)
      return "seq=" .. seq .. "\nunit=1\nx=1\nz=1\nrun=1\nend\n"
    end
    local first = twllm_parse_orders(with_seq("1793506662635"))
    local second = twllm_parse_orders(with_seq("1793506672640"))
    assert.are.equal("1793506662635", first.seq_text)
    assert.are.equal("1793506672640", second.seq_text)
    assert.is_true(first.seq_text ~= second.seq_text)
  end)

  it("parses when math.huge and math.floor are missing", function()
    local saved_huge = math.huge
    local saved_floor = math.floor
    math.huge = nil
    math.floor = nil
    local ok, err = pcall(function()
      dofile("game/napoleon/lodi_battle.battle_script")
      local order, reason = twllm_parse_orders(fixture)
      assert.is_nil(reason)
      assert.are.equal(1730400000000, order.seq)
      assert.are.equal("1730400000000", order.seq_text)
      assert.is_true(order.run)
      assert_rejected(replace_value(fixture, "x", "inf"))
      assert_rejected(replace_value(fixture, "x", "nan"))
      assert_rejected(replace_value(fixture, "unit", "1.5"))
      assert_rejected(replace_value(fixture, "seq", "-3"))
    end)
    math.huge = saved_huge
    math.floor = saved_floor
    if not ok then error(err, 0) end
  end)

  it("rejects text over 4096 bytes", function()
    local text = "seq=1\nunit=1\nx=0\nz=0\nrun=1\nfoo=" .. string.rep("a", 5000) .. "\nend\n"
    assert.is_true(#text > 4096)
    assert_rejected(text)
  end)
end)
