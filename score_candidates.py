base = {'Life':3620,'Armour':17253,'ChaosResist':-1,'TotalEHP':23344.142589968,'TotalDPS':203075.41643061,'ChaosMaximumHitTaken':6615}
body = {'Life':3620,'Armour':17253,'ChaosResist':29,'TotalEHP':25844.184129281,'TotalDPS':203075.41643061,'ChaosMaximumHitTaken':9411}
charge = {'Life':3620,'Armour':17253,'ChaosResist':-1,'TotalEHP':23344.142589968,'TotalDPS':206503.05231064,'ChaosMaximumHitTaken':6615}
for name, item in [('胸甲補混沌抗性', body), ('Charge Mastery 改三種 Charge 增傷', charge)]:
    print(name)
    for key in base:
        if item[key] != base[key]:
            print(key, 'delta=', round(item[key]-base[key], 4), 'pct=', round((item[key]/base[key]-1)*100, 3) if base[key] else None)
print('Warcry recovery=', 3620*0.15)
