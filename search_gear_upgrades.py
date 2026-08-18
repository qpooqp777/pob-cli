from __future__ import annotations
import itertools, json, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from pob_cli.headless import run_pob_calcs
from pob_cli.power_report import build_power_report
ROOT=Path('/home/ubuntu/pob-cli'); POB=Path('/home/ubuntu/PathOfBuilding'); base=(ROOT/'attached_build.xml').read_text()
BASE_SKILL='Creeping Frost'
BASE_PAYLOAD=run_pob_calcs(ROOT/'attached_build.xml', POB, skill=BASE_SKILL, include_skills=True)
BASE_OUTPUT=BASE_PAYLOAD['output']
baseline={'dps':BASE_OUTPUT.get('TotalDPS',0),'ehp':BASE_OUTPUT.get('TotalEHP',0),'ab':BASE_OUTPUT.get('EffectiveAverageBlockChance',0),'sb':BASE_OUTPUT.get('EffectiveSpellBlockChance',0),'life':BASE_OUTPUT.get('Life',0),'es':BASE_OUTPUT.get('EnergyShield',0),'armour':BASE_OUTPUT.get('Armour',0)}
# These are replacement targets, not claims that the current unique item can receive arbitrary mods.
amulets={
 'amulet_cold1':['+1 to Level of all Cold Skill Gems'],
 'amulet_dot20':['+20% to Cold Damage over Time Multiplier'],
 'amulet_cold1_dot20':['+1 to Level of all Cold Skill Gems','+20% to Cold Damage over Time Multiplier'],
 'amulet_spell1_dot20':['+1 to Level of all Spell Skill Gems','+20% to Cold Damage over Time Multiplier'],
 'amulet_cold1_dot35':['+1 to Level of all Cold Skill Gems','+35% to Cold Damage over Time Multiplier'],
 'amulet_cold1_dot50':['+1 to Level of all Cold Skill Gems','+50% to Cold Damage over Time Multiplier'],
}
weapons={
 'weapon_spell1':['+1 to Level of all Spell Skill Gems'],
 'weapon_dot30':['+30% to Cold Damage over Time Multiplier'],
 'weapon_spell1_dot30':['+1 to Level of all Spell Skill Gems','+30% to Cold Damage over Time Multiplier'],
 'weapon_spell1_dot60':['+1 to Level of all Spell Skill Gems','+60% to Cold Damage over Time Multiplier'],
 'weapon_cold1_dot30':['+1 to Level of all Cold Skill Gems','+30% to Cold Damage over Time Multiplier'],
 'weapon_spell1_dot50_cast10':['+1 to Level of all Spell Skill Gems','+50% to Cold Damage over Time Multiplier','10% increased Cast Speed'],
}
def make_xml(amulet_mods, weapon_mods):
    x=base
    if amulet_mods:
        marker='+95 to maximum Life\n'
        if marker not in x: raise RuntimeError('amulet marker missing')
        x=x.replace(marker,marker+'\n'.join(amulet_mods)+'\n',1)
    if weapon_mods:
        marker='31% increased Projectile Damage\n'
        if marker not in x: raise RuntimeError('weapon marker missing')
        x=x.replace(marker,marker+'\n'.join(weapon_mods)+'\n',1)
    return x
def run(name, ammods, wmods):
    xml=make_xml(ammods,wmods)
    with tempfile.NamedTemporaryFile('w',suffix='.xml',prefix='pob_gear_',delete=False) as f:
        f.write(xml); fn=f.name
    try:
        candidate_payload=run_pob_calcs(fn, POB, skill=BASE_SKILL, include_skills=True)
        o=candidate_payload['output']; row={'name':name,'amulet_mods':ammods,'weapon_mods':wmods}
        for k,outk in [('dps','TotalDPS'),('ehp','TotalEHP'),('ab','EffectiveAverageBlockChance'),('sb','EffectiveSpellBlockChance'),('life','Life'),('es','EnergyShield'),('armour','Armour'),('cold_dot','ColdDot'),('cold_max','ColdMaximumHitTaken'),('phys_max','PhysicalMaximumHitTaken')]: row[k]=o.get(outk,0)
        row['selected_skill']=candidate_payload.get('selected_skill')
        row['skill_context']=candidate_payload.get('skill_sets')
        row['power_report']=build_power_report(BASE_PAYLOAD, candidate_payload, {'selected_skill':BASE_PAYLOAD.get('selected_skill'),'skill_sets':BASE_PAYLOAD.get('skill_sets')}, {'selected_skill':candidate_payload.get('selected_skill'),'skill_sets':candidate_payload.get('skill_sets')})
        row['dps_pct']=100*(row['dps']/baseline['dps']-1); row['ehp_pct']=100*(row['ehp']/baseline['ehp']-1)
        row['pass']=row['dps_pct']>=3 and row['ehp']>=.95*baseline['ehp'] and row['ab']>=70 and row['sb']>=70
        return row
    except Exception as exc:
        return {'name':name,'error':str(exc)}
    finally: Path(fn).unlink(missing_ok=True)
tasks=[('baseline',[],[])]
for an,am in amulets.items(): tasks.append((an,am,[]))
for wn,wm in weapons.items(): tasks.append((wn,[],wm))
for an,am in amulets.items():
 for wn,wm in weapons.items(): tasks.append((an+'+'+wn,am,wm))
results=[]
with ThreadPoolExecutor(max_workers=6) as ex:
 futs=[ex.submit(run,*t) for t in tasks]
 for f in as_completed(futs): results.append(f.result())
results=[x for x in results if 'error' not in x]
results.sort(key=lambda x:(x['pass'],x['dps_pct']),reverse=True)
Path('/tmp/gear_upgrade_search_results.json').write_text(json.dumps({'baseline':baseline,'results':results},ensure_ascii=False,indent=2))
passed=[x for x in results if x['pass']]
print('tested',len(results),'passed',len(passed))
for x in passed[:20]: print('PASS',json.dumps(x,ensure_ascii=False))
print('TOP',json.dumps(results[:10],ensure_ascii=False))
