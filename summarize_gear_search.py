import json
p=json.loads(open('/tmp/gear_upgrade_search_results.json').read()); r=p['results']
print('tested',len(r),'passed',sum(x['pass'] for x in r))
for title, rows in [('single',[x for x in r if '+' not in x['name']]),('combo',[x for x in r if '+' in x['name']])]:
 print('\n'+title)
 for x in sorted(rows,key=lambda z:z['dps_pct'],reverse=True)[:15]:
  print(x['name'], 'dps_pct=',round(x['dps_pct'],2),'ehp_pct=',round(x['ehp_pct'],2),'ab=',x['ab'],'sb=',x['sb'],'dps=',round(x['dps'],2),'cold_dot=',round(x['cold_dot'],2),'mods=',x.get('amulet_mods'),x.get('weapon_mods'))
