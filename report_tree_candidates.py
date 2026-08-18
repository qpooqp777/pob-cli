import json
keys=['Life','EnergyShield','Armour','TotalEHP','TotalDPS','CombinedDPS','ColdDot','ColdMaximumHitTaken','PhysicalMaximumHitTaken','EffectiveAverageBlockChance','EffectiveSpellBlockChance']
for n in ['attached_calc','path_breath_of_rime','path_coldhearted','path_trickery','path_doom_cast','path_snowforged']:
 p=json.load(open('/tmp/'+n+'.json'))['output']; print('\n'+n)
 for k in keys:
  if k in p: print(k,p[k])
