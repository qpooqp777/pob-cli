io.stdout:setvbuf("no")
local buildPath = arg[1]
local function readAll(path)
  local f = assert(io.open(path, "rb"))
  local data = f:read("*a")
  f:close()
  return data
end

print("POB_HEADLESS_START")
dofile(arg[2] .. "/HeadlessWrapper.lua")
print("POB_HEADLESS_READY")
loadBuildFromXML(readAll(buildPath), buildPath)
print("POB_BUILD_LOADED")
build.calcsTab:BuildOutput()
print("POB_CALCS_DONE")
local out = build.calcsTab.calcsOutput or {}
local keys = {}
for k, v in pairs(out) do
  if type(v) ~= "table" and type(v) ~= "function" then
    keys[#keys + 1] = tostring(k) .. "=" .. tostring(v)
  end
end
table.sort(keys)
for _, line in ipairs(keys) do print(line) end
