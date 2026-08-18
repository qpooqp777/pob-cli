from pathlib import Path
import re
p=Path('/home/ubuntu/PathOfBuilding/src/TreeData/3_29/tree.lua').read_text()
for name in ['Coldhearted Calculation','Snowforged','Trickery','Coordination','Sovereignty','Whispers of Doom','Doom Cast','Breath of Rime','Snowstorm','Frost Walker','Heart of Ice']:
    pos=p.find('["name"] = "'+name+'"')
    if pos<0: pos=p.find('["name"]= "'+name+'"')
    if pos<0:
        print(name,'NOT FOUND'); continue
    start=p.rfind('{',0,pos-500)
    end=p.find('\n            },',pos)+14
    chunk=p[start:end]
    ids=re.findall(r'\["id"\]\s*=\s*(\d+)',chunk)
    print('\n###',name,'ids',ids)
    print(chunk[:1600].replace('\n',' '))
