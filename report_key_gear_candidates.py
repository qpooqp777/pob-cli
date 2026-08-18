import json
p=json.loads(open('/tmp/gear_upgrade_search_results.json').read())
keys=['amulet_cold1','amulet_spell1_dot20','weapon_spell1','weapon_spell1_dot30','weapon_cold1_dot30','amulet_cold1+weapon_spell1','amulet_spell1_dot20+weapon_spell1_dot30']
for k in keys:
 x=next((r for r in p['results'] if r['name']==k),None)
 print(k, x)
