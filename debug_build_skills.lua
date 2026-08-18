local buildPath = arg[1]
local pobRoot = arg[2]
local f = assert(io.open(buildPath, "rb"))
local xml = f:read("*a")
f:close()
dofile(pobRoot .. "/src/HeadlessWrapper.lua")
loadBuildFromXML(xml, buildPath)
print("sections=" .. tostring(#(build.xmlSectionList or {})))
for i, node in ipairs(build.xmlSectionList or {}) do
  print(" section=" .. tostring(i) .. " elem=" .. tostring(node.elem) .. " children=" .. tostring(#node))
  if node.elem == "Skills" then for j, child in ipairs(node) do print("  child=" .. tostring(j) .. " elem=" .. tostring(child.elem) .. " children=" .. tostring(#child)) end end
end
print("skillSets=" .. tostring(#(build.skillsTab.skillSetOrderList or {})))
for _, setId in ipairs(build.skillsTab.skillSetOrderList or {}) do
  local set = build.skillsTab.skillSets[setId]
  print("set=" .. tostring(setId) .. " groups=" .. tostring(#(set.socketGroupList or {})))
  for i, group in ipairs(set.socketGroupList or {}) do
    print(" group=" .. tostring(i) .. " slot=" .. tostring(group.slot) .. " gems=" .. tostring(#(group.gemList or {})))
    for j, gem in ipairs(group.gemList or {}) do
      print("  gem=" .. tostring(j) .. " name=" .. tostring(gem.nameSpec) .. " skill=" .. tostring(gem.skillId) .. " gemId=" .. tostring(gem.gemId))
    end
  end
end
