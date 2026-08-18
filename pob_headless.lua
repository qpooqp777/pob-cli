-- pob CLI headless bridge for Path of Building Community Fork.
-- Usage: luajit pob_headless.lua <build.xml> <pob-src-dir>

io.stdout:setvbuf("no")
local buildPath = assert(arg[1], "missing build XML")
local pobSrc = assert(arg[2], "missing PoB src directory")

local function readAll(path)
  local f, err = io.open(path, "rb")
  assert(f, err)
  local data = f:read("*a")
  f:close()
  return data
end

-- HeadlessWrapper resolves files relative to PoB/src. The Python launcher
-- starts this process with cwd set to that directory.
dofile(pobSrc .. "/HeadlessWrapper.lua")

-- Keep diagnostic output off stdout so Python can consume the final JSON line.
local function diagnostic(fmt, ...)
  io.stderr:write((select("#", ...) > 0 and string.format(fmt, ...) or tostring(fmt)) .. "\n")
end
ConPrintf = diagnostic
ConClear = function() end

local requestedSkill = arg[3]
local configJson = arg[4]
local includeBreakdown = arg[5] == "breakdown"
local includeConfigOptions = arg[5] == "config-options" or arg[6] == "config-options"
local includeSkills = arg[5] == "skills" or arg[6] == "skills"
local json = require("dkjson")
local selectedSkill = nil
local availableSkills = {}

local function selectSkillByName(name)
  if not name or name == "" then return end
  local needle = string.lower(name)
  for groupIndex, group in ipairs(build.skillsTab.socketGroupList or {}) do
    local skillList = group.displaySkillListCalcs or group.displaySkillList or {}
    for skillIndex, skill in ipairs(skillList) do
      local granted = skill.activeEffect and skill.activeEffect.grantedEffect
      local skillName = granted and granted.name
      if skillName then
        availableSkills[#availableSkills + 1] = skillName
        if string.lower(skillName) == needle or string.find(string.lower(skillName), needle, 1, true) then
          build.calcsTab.input.skill_number = groupIndex
          group.mainActiveSkillCalcs = skillIndex
          selectedSkill = skillName
          return
        end
      end
    end
  end
  error("找不到技能：" .. name)
end

local ok, err = pcall(function()
  loadBuildFromXML(readAll(buildPath), buildPath)
  assert(build and build.calcsTab, "PoB Build/CalcsTab was not initialised")
  if configJson and #configJson > 0 then
    local config = json.decode(configJson)
    assert(type(config) == "table", "Config JSON 必須是 object")
    local configTab = build.configTab
    local configSet = configTab.configSets[configTab.activeConfigSetId]
    assert(configSet and configSet.input, "PoB ConfigSet 尚未初始化")
    for key, value in pairs(config) do
      configSet.input[key] = value
    end
    configTab:BuildModList()
  end
  selectSkillByName(requestedSkill)
  build.calcsTab:BuildOutput()
end)

if not ok then
  io.write(json.encode({ ok = false, error = tostring(err) }) .. "\n")
  os.exit(1)
end

local source = build.calcsTab.calcsOutput or {}
local output = {}
for key, value in pairs(source) do
  local kind = type(value)
  if kind == "number" or kind == "string" or kind == "boolean" then
    if kind ~= "number" or (value == value and value ~= math.huge and value ~= -math.huge) then
      output[key] = value
    end
  end
end

local function serialiseValue(value, depth, seen)
  if depth > 6 then return "<max-depth>" end
  local kind = type(value)
  if kind == "number" then
    if value == value and value ~= math.huge and value ~= -math.huge then return value end
    return nil
  elseif kind == "string" or kind == "boolean" then
    return value
  elseif kind ~= "table" then
    return nil
  end
  seen = seen or {}
  if seen[value] then return "<cycle>" end
  seen[value] = true
  local out = {}
  for key, child in pairs(value) do
    if key ~= "item" and key ~= "modDB" and key ~= "actor" and key ~= "build" then
      local safeKey = type(key) == "string" and key or tostring(key)
      local safeValue = serialiseValue(child, depth + 1, seen)
      if safeValue ~= nil then out[safeKey] = safeValue end
    end
  end
  seen[value] = nil
  return out
end

local function classifyGem(name, variantId, gameId, isSupport)
  name = name or ""
  variantId = variantId or ""
  gameId = gameId or ""
  if isSupport then return "support" end
  if name:match("^[Aa]wakened ") or gameId:find("Awakened", 1, true) or variantId:match("^Awakened") then return "awakened" end
  if variantId:match("Alt[XYZ]$") then return "transfigured" end
  if variantId:match("^Vaal") or gameId:find("Vaal", 1, true) then return "vaal" end
  return "active"
end

local skillSets
if includeSkills then
  skillSets = {}
  for setId, skillSet in pairs(build.skillsTab.skillSets or {}) do
    local setOut = { id = tonumber(setId) or setId, title = skillSet.title, groups = {} }
    for groupIndex, group in ipairs(skillSet.socketGroupList or {}) do
      local groupOut = {
        index = groupIndex,
        slot = group.slot,
        label = group.label,
        enabled = group.enabled,
        includeInFullDPS = group.includeInFullDPS,
        mainActiveSkill = group.mainActiveSkill,
        mainActiveSkillCalcs = group.mainActiveSkillCalcs,
        groupCount = group.groupCount,
        gems = {},
      }
      for gemIndex, gem in ipairs(group.gemList or {}) do
        local data = gem.gemData or {}
        local gameId = data.gameId or gem.gemId
        local isSupport = gameId and gameId:find("/SupportGem", 1, true) ~= nil or false
        local variantType = classifyGem(gem.nameSpec or data.name, data.variantId or gem.variantId, gameId, isSupport)
        local gemOut = {
          index = gemIndex,
          name = gem.nameSpec or data.name,
          skillId = gem.skillId,
          gemId = gameId,
          variantId = data.variantId or gem.variantId,
          level = gem.level,
          quality = gem.quality,
          enabled = gem.enabled,
          enableGlobal1 = gem.enableGlobal1,
          enableGlobal2 = gem.enableGlobal2,
          count = gem.count,
          skillPart = gem.skillPart,
          skillPartCalcs = gem.skillPartCalcs,
          skillStageCount = gem.skillStageCount,
          skillStageCountCalcs = gem.skillStageCountCalcs,
          skillMineCount = gem.skillMineCount,
          skillMineCountCalcs = gem.skillMineCountCalcs,
          skillMinion = gem.skillMinion,
          skillMinionCalcs = gem.skillMinionCalcs,
          skillMinionItemSet = gem.skillMinionItemSet,
          skillMinionItemSetCalcs = gem.skillMinionItemSetCalcs,
          skillMinionSkill = gem.skillMinionSkill,
          skillMinionSkillCalcs = gem.skillMinionSkillCalcs,
          minionContext = (gem.skillMinion or gem.skillMinionCalcs or gem.skillMinionItemSet or gem.skillMinionItemSetCalcs or gem.skillMinionSkill or gem.skillMinionSkillCalcs) and {
            minionId = gem.skillMinion,
            minionIdCalcs = gem.skillMinionCalcs,
            itemSetId = gem.skillMinionItemSet,
            itemSetIdCalcs = gem.skillMinionItemSetCalcs,
            activeSkillIndex = gem.skillMinionSkill,
            activeSkillIndexCalcs = gem.skillMinionSkillCalcs,
            minionTypes = data.grantedEffect and data.grantedEffect.minionList or nil,
            contextSource = "PoB SkillsTab gem instance + grantedEffect.minionList",
          } or nil,
          gemType = variantType,
          classificationSource = variantType == "transfigured" and "variantId:AltX/AltY/AltZ" or (variantType == "awakened" and "name/gameId/variantId" or (variantType == "support" and "gameId:/SupportGem" or "variantId/gameId")),
          baseTypeName = data.baseTypeName,
          tags = data.tagString,
          grantedEffectId = data.grantedEffectId,
          naturalMaxLevel = data.naturalMaxLevel,
          reqStr = data.reqStr,
          reqDex = data.reqDex,
          reqInt = data.reqInt,
        }
        groupOut.gems[#groupOut.gems + 1] = gemOut
      end
      groupOut.mainGem = groupOut.gems[groupOut.mainActiveSkill or 1] and groupOut.gems[groupOut.mainActiveSkill or 1].name or nil
      setOut.groups[#setOut.groups + 1] = groupOut
    end
    skillSets[#skillSets + 1] = setOut
  end
  table.sort(skillSets, function(a, b) return tostring(a.id) < tostring(b.id) end)
end

local configOptions
if includeConfigOptions then
  local varList = LoadModule("Modules/ConfigOptions")
  local visibility = LoadModule("Modules/ConfigVisibility")
  configOptions = {}
  for _, varData in ipairs(varList or {}) do
    if varData.var and visibility.isRelevantForBuild(varData, build) then
      local option = {
        var = varData.var,
        type = varData.type,
        label = varData.label,
        defaultState = varData.defaultState,
        defaultPlaceholderState = varData.defaultPlaceholderState,
      }
      if varData.list then
        option.values = {}
        for _, item in ipairs(varData.list) do
          option.values[#option.values + 1] = { label = item.label, value = item.val }
        end
      end
      configOptions[#configOptions + 1] = option
    end
  end
end

local result = {
  ok = true,
  engine = "Path of Building Community Fork",
  tree = build.spec and build.spec.tree and build.spec.tree.treeVersion or nil,
  level = build.level,
  class = build.characterClassName,
  selected_skill = selectedSkill,
  available_skills = availableSkills,
  output = output,
  breakdown = includeBreakdown and serialiseValue(build.calcsTab.calcsEnv.player.breakdown, 0, {}) or nil,
  config_options = configOptions,
  skill_sets = skillSets,
}
io.write(json.encode(result) .. "\n")
