local buildPath = assert(arg[1])
local pobSrc = assert(arg[2])
dofile(pobSrc .. "/HeadlessWrapper.lua")
ConPrintf = function(...) end
ConClear = function() end
loadBuildFromXML(io.open(buildPath):read("*a"), buildPath)
build.calcsTab:BuildOutput()
local actor = build.calcsTab.calcsEnv and build.calcsTab.calcsEnv.player
print("actor", actor ~= nil)
for k,v in pairs(actor and actor.breakdown or {}) do print("breakdown", k, type(v)) end
for i,section in ipairs(build.calcsTab.displayData or {}) do print("display", i, section.label or "", section.breakdown or "", section.modName or "") end
