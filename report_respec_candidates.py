import json
keys=['Life','EnergyShield','Armour','TotalEHP','TotalDPS','CombinedDPS','ColdDot','ColdMaximumHitTaken','PhysicalMaximumHitTaken','EffectiveAverageBlockChance','EffectiveSpellBlockChance','EffectiveMovementSpeedMod']
for n in ['attached_calc','respec_doom_cast','respec_snowforged','respec_coldhearted_trickery']:
 p=json.load(open('/tmp/'+n+'.json'))['output']; print('\n'+n)
 for k in keys:
  if k in p: print(k,p[k])
