from __future__ import annotations
import json
from pathlib import Path
p=json.loads(Path('/tmp/hc_tree_search_results.json').read_text())
results=p['results']
passed=[x for x in results if x['pass']]
print('tested',len(results),'passed',len(passed))
print('baseline',p['baseline'])
if passed:
    for x in passed[:20]: print('PASS',json.dumps(x,ensure_ascii=False))
print('\nBEST DPS SUBJECT TO DEFENCE')
eligible=[x for x in results if x['ehp']>=.95*p['baseline']['ehp'] and x['ab']>=70 and x['sb']>=70]
for x in sorted(eligible,key=lambda r:r['dps_pct'],reverse=True)[:15]: print(json.dumps(x,ensure_ascii=False))
print('\nCLOSEST BY DPS GAP WITH DEFENCE')
for x in sorted(eligible,key=lambda r:r['dps_pct'],reverse=True)[:10]: print(json.dumps(x,ensure_ascii=False))
