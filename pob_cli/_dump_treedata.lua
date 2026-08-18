local path = arg[1]
local tree = dofile(path)

local function esc(s)
  s = tostring(s)
  s = s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r'):gsub('\t', '\\t')
  return '"' .. s .. '"'
end

local function json(v)
  local t = type(v)
  if t == 'nil' then return 'null' end
  if t == 'boolean' then return v and 'true' or 'false' end
  if t == 'number' then return tostring(v) end
  if t == 'string' then return esc(v) end
  if t ~= 'table' then return 'null' end
  local is_array = true
  local max = 0
  for k, _ in pairs(v) do
    if type(k) ~= 'number' or k < 1 or k % 1 ~= 0 then is_array = false break end
    if k > max then max = k end
  end
  local out = {}
  if is_array then
    for i = 1, max do out[#out + 1] = json(v[i]) end
    return '[' .. table.concat(out, ',') .. ']'
  end
  for k, value in pairs(v) do
    out[#out + 1] = esc(k) .. ':' .. json(value)
  end
  return '{' .. table.concat(out, ',') .. '}'
end

local out = {tree = tree.tree, classes = {}, nodes = {}}
for i, class in ipairs(tree.classes or {}) do
  local c = {name = class.name, nodes = class.nodes or {}}
  out.classes[#out.classes + 1] = c
end
for id, node in pairs(tree.nodes or {}) do
  out.nodes[tostring(id)] = {
    skill = node.skill,
    name = node.name,
    out = node.out or {},
    ["in"] = node["in"] or {},
    isMastery = node.isMastery or false,
    isJewelSocket = node.isJewelSocket or false,
    group = node.group,
    classStartIndex = node.classStartIndex,
    classStart = node.classStart or false
  }
end
io.write(json(out))
