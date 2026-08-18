from pathlib import Path
import re
p=Path('/home/ubuntu/PathOfBuilding/src/TreeData/3_29/tree.lua').read_text()
for name in ['Coldhearted Calculation','Snowforged','Trickery','Coordination','Sovereignty','Whispers of Doom','Doom Cast','Breath of Rime','Snowstorm']:
    m=re.search(r'\[(\d+)\]\s*=\s*\{(?:(?!\n\s*\[\d+\]\s*=).)*?\["name"\]\s*=\s*"'+re.escape(name)+r'"(?:(?!\n\s*\[\d+\]\s*=).)*',p,re.S)
    if not m:
        print(name,'NOT FOUND'); continue
    chunk=m.group(0)
    print('\n###',name,'node=',m.group(1))
    print(re.sub(r'\s+',' ',chunk[-1100:]))
