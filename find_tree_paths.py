from pathlib import Path
import re, collections, xml.etree.ElementTree as ET
p=Path('/home/ubuntu/PathOfBuilding/src/TreeData/3_29/tree.lua').read_text()
nodes={}
for m in re.finditer(r'^\s*\[(\d+)\]\s*=\s*\{(.*?)(?=^\s*\[\d+\]\s*=\s*\{|^\s*\},\s*$)',p,re.M|re.S):
    nid=m.group(1); b=m.group(2)
    name=re.search(r'\["name"\]\s*=\s*"([^"]+)"',b)
    outs=re.findall(r'\["out"\]\s*=\s*\{(.*?)\}',b,re.S)
    ins=re.findall(r'\["in"\]\s*=\s*\{(.*?)\}',b,re.S)
    adj=set()
    for txt in outs+ins: adj.update(re.findall(r'"(\d+)"',txt))
    nodes[nid]={'name':name.group(1) if name else '', 'adj':adj}
# add reverse edges
for nid,d in list(nodes.items()):
  for other in d['adj']:
    if other in nodes: nodes[other]['adj'].add(nid)
root=ET.parse('/home/ubuntu/pob-cli/attached_build.xml').getroot()
spec=root.find('Tree/Spec') or root.find('.//Spec')
cur=set(re.sub(r'\s+','',spec.attrib['nodes']).split(','))
print('current nodes',len(cur),'parsed tree nodes',len(nodes))
for target in ['24050','35894','61981','21460','42649','22535','40870']:
  q=collections.deque(cur); prev={x:None for x in cur}; hit=None
  while q:
    x=q.popleft()
    if x==target: hit=x; break
    for y in nodes.get(x,{}).get('adj',[]):
      if y not in prev:
        prev[y]=x; q.append(y)
  if hit:
    path=[]
    while hit is not None: path.append(hit); hit=prev[hit]
    path=path[::-1]
    print(target,nodes.get(target,{}).get('name'),'path',len(path)-1,path)
  else: print(target,'NO PATH')
