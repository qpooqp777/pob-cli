from __future__ import annotations
import itertools, json, re, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT=Path('/home/ubuntu/pob-cli'); BASE=ROOT/'attached_build.xml'; POB=Path('/home/ubuntu/PathOfBuilding')
base=BASE.read_text(); m=re.search(r'(<Spec[^>]*\bnodes=")([^"]+)("[^>]*>)',base)
if not m: raise SystemExit('Spec nodes not found')
cur=[x for x in m.group(2).replace('\n','').split(',') if x]
# Valid shortest paths from the current tree to candidate damage nodes, discovered from PoB 3.29 tree.lua.
paths={
 'Snowforged':['4502','20852','6785','42649'],
 'Doom Cast':['61653','36858','60405','25757','61981'],
 'Coldhearted Calculation':['4502','33783','3656','24050'],
 'Trickery':['4502','33783','3656','20546','35894'],
 'Breath of Rime':['60170','21460'],
 'Whispers of Doom':['49605','60440','30767','32314','43010','22535'],
}
# Terminal or low-impact candidates only; shield/block/life/ES/core nodes are deliberately excluded.
removable=['57197','61308','14745','9586','53493','14113','20528']
# Baseline is already calculated by pob CLI; these fields are the hard constraints.
baseline={'dps':442240.55025127,'ehp':101832.70907909,'ab':74.0,'sb':73.0}
def run(name, add_path, remove):
    nodes=[x for x in cur if x not in remove]
    for x in add_path:
        if x not in nodes: nodes.append(x)
    xml=base[:m.start(2)]+','.join(nodes)+base[m.end(2):]
    with tempfile.NamedTemporaryFile('w',suffix='.xml',prefix='pob_search_',delete=False) as f:
        f.write(xml); fn=f.name
    try:
        r=subprocess.run(['python3','-m','pob_cli','calc',fn,'--pob-root',str(POB),'--format','json'],cwd=ROOT,text=True,capture_output=True,timeout=180)
        if r.returncode: return {'name':name,'remove':remove,'error':r.stderr[-500:]}
        p=json.loads(r.stdout)['output']
        row={'name':name,'remove':remove,'add':[x for x in add_path if x not in cur],
             'dps':p.get('TotalDPS',0),'ehp':p.get('TotalEHP',0),'ab':p.get('EffectiveAverageBlockChance',0),'sb':p.get('EffectiveSpellBlockChance',0),
             'cold_dot':p.get('ColdDot',0),'life':p.get('Life',0),'es':p.get('EnergyShield',0)}
        row['dps_pct']=100*(row['dps']/baseline['dps']-1); row['ehp_pct']=100*(row['ehp']/baseline['ehp']-1)
        row['pass']=row['dps_pct']>=3 and row['ehp']>=.95*baseline['ehp'] and row['ab']>=70 and row['sb']>=70
        return row
    finally:
        Path(fn).unlink(missing_ok=True)

tasks=[]
for name,path in paths.items():
 add=[x for x in path if x not in cur]
 if not add: continue
 for rem in itertools.combinations(removable,len(add)):
  tasks.append((name,path,list(rem)))
results=[]
with ThreadPoolExecutor(max_workers=6) as ex:
 futs=[ex.submit(run,*t) for t in tasks]
 for f in as_completed(futs): results.append(f.result())
results=[x for x in results if 'error' not in x]
results.sort(key=lambda x:(x['pass'],x['dps_pct'],x['ehp_pct']),reverse=True)
Path('/tmp/hc_tree_search_results.json').write_text(json.dumps({'baseline':baseline,'results':results},ensure_ascii=False,indent=2))
passed=[x for x in results if x['pass']]
print('tested',len(results),'passed',len(passed))
print('TOP')
for x in results[:20]: print(json.dumps(x,ensure_ascii=False))
