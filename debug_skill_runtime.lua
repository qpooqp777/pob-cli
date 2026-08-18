local buildPath = assert(arg[1])
local src = assert(arg[2])
dofile(src .. "/HeadlessWrapper.lua")
ConPrintf = function(...) end
ConClear = function() end
loadBuildFromXML(io.open(buildPath):read("*a"), buildPath)
for setId, set in pairs(build.skillsTab.skillSets or {}) do
  print("SET", setId, set.title or "", #set.socketGroupList)
  for idx, group in ipairs(set.socketGroupList or {}) do
    print("GROUP", idx, group.slot or "", tostring(group.enabled), tostring(group.mainActiveSkill), tostring(group.includeInFullDPS), #group.gemList)
    for gi, gem in ipairs(group.gemList or {}) do
      local d = gem.gemData or {}
      print("GEM", gi, gem.nameSpec or "", gem.skillId or "", gem.level or "", gem.quality or "", tostring(gem.enabled), d.gameId or "", d.variantId or "", tostring(d.isSupport), d.name or "", d.tags and table.concat(d.tags, ",") or "")
    end
  end
end
