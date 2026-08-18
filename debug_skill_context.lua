local buildPath = assert(arg[1])
local src = assert(arg[2])
dofile(src .. "/HeadlessWrapper.lua")
ConPrintf = function(...) end
ConClear = function() end
loadBuildFromXML(io.open(buildPath):read("*a"), buildPath)
local env = build.calcsTab.calcsEnv
local player = env.player or {}
print("PLAYER_MAIN", player.mainSkill and player.mainSkill.skillData and player.mainSkill.skillData.name or "")
for setId, skillSet in pairs(build.skillsTab.skillSets or {}) do
  for gi, group in ipairs(skillSet.socketGroupList or {}) do
    for mi, gem in ipairs(group.gemList or {}) do
      if gem.skillMinion or gem.skillPart or gem.skillStageCount or gem.skillMineCount then
        print("GEMCTX", group.slot or "", mi, gem.nameSpec or "", "part", gem.skillPart or "", gem.skillPartCalcs or "", "stage", gem.skillStageCount or "", gem.skillStageCountCalcs or "", "mine", gem.skillMineCount or "", gem.skillMineCountCalcs or "", "minion", gem.skillMinion or "", gem.skillMinionCalcs or "", "minionSkill", gem.skillMinionSkill or "", gem.skillMinionSkillCalcs or "")
        local minionId = gem.skillMinionCalcs or gem.skillMinion
        if minionId and player.minionList then
          for _, minion in ipairs(player.minionList) do
            if minion.id == minionId or minion.minionId == minionId then
              print("MINION", minionId, minion.mainSkill and minion.mainSkill.skillData and minion.mainSkill.skillData.name or "", #minion.activeSkillList)
              for ai, active in ipairs(minion.activeSkillList or {}) do
                print("ACTIVESKILL", ai, active.skillData and active.skillData.name or "", active.skillData and active.skillData.id or "")
              end
            end
          end
        end
      end
    end
  end
end
