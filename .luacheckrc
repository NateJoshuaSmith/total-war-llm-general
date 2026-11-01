-- Napoleon's Lua is 5.1 with math.huge missing. Game files use this standard
-- on its own (not added on top of lua51) so math.huge is an undefined field.
std = "lua51"

include_files = {
  "**/*.lua",
  "**/*.battle_script",
}

exclude_files = {
  "game/napoleon/phase0_*",
}

stds.napoleon = {
  globals = {
    "battle",
    "twllm_tick",
    "BattlePhaseChange",
    "twllm_parse_orders",
    "TWLLM_TEST",
  },
  read_globals = {
    "_G",
    "_VERSION",
    "arg",
    "assert",
    "collectgarbage",
    "coroutine",
    "debug",
    "dofile",
    "error",
    "getfenv",
    "getmetatable",
    "io",
    "ipairs",
    "load",
    "loadfile",
    "loadstring",
    "module",
    "newproxy",
    "next",
    "os",
    "package",
    "pairs",
    "pcall",
    "print",
    "rawequal",
    "rawget",
    "rawset",
    "require",
    "select",
    "setfenv",
    "setmetatable",
    "string",
    "table",
    "tonumber",
    "tostring",
    "type",
    "unpack",
    "xpcall",
    "empire_battle",
    "battle_vector",
    math = {
      fields = {
        "abs",
        "acos",
        "asin",
        "atan",
        "atan2",
        "ceil",
        "cos",
        "cosh",
        "deg",
        "exp",
        "floor",
        "fmod",
        "frexp",
        "ldexp",
        "log",
        "log10",
        "max",
        "min",
        "mod",
        "modf",
        "pi",
        "pow",
        "rad",
        "random",
        "randomseed",
        "sin",
        "sinh",
        "sqrt",
        "tan",
        "tanh",
      },
    },
  },
}

files["game"] = {
  std = "napoleon",
}

files["tests/lua"] = {
  std = "lua51+busted",
}
