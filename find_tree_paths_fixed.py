from pathlib import Path
import re, collections, xml.etree.ElementTree as ET
p=Path('/home/ubuntu/PathOfBuilding/src/TreeData/3_29/tree.lua').read_text()
starts=list(re.finditer(r'^\s*\[(\d+)\]\s*=\s*\{',p,re.M))
nodes={}
for i,m in enumerate(starts):
    nid=m.group(1); end=starts[i+1].start() if i+1<len(starts) else len(p); b=p[m.end():end]
    name=re.search(r'\["name"\]\s*=\s*"([^"]+)"',b)
    adj=set()
    for key in ['out','in']:
        for mm in re.finditer(r'\["'+key+r'"\]\s*=\s*\{(.*?)\}',b,re.S): adj.update(re.findall(r'"(\d+)"',mm.group(1)))
    nodes[nid]={'name':name.group(1) if name else '', 'adj':adj}
for nid,d in list(nodes.items()):
  for other in d['adj']:
    if other in nodes: nodes[other]['adj'].add(nid)
root=ET.parse('/home/ubuntu/pob-cli/attached_build.xml').getroot(); spec=root.find('.//Spec')
cur=set(re.sub(r'\s+','',spec.attrib['nodes']).split(','))
print('current',len(cur),'nodes',len(nodes),'edges',sum(len(x['adj']) for x in nodes.values()))
for target in ['24050','35894','61981','21460','42649','22535','40870']:
  q=collections.deque(cur); prev={x:None for x in cur}; hit=None
  while q:
    x=q.popleft()
    if x==target: hit=x; break
    for y in nodes.get(x,{}).get('adj',[]):
      if y not in prev: prev[y]=x; q.append(y)
  if hit:
    path=[]
    while hit is not None: path.append(hit); hit=prev[hit]
    path=path[::-1]
    print(target,nodes.get(target,{}).get('name'),'path',len(path)-1,path)
  else: print(target,'NO PATH')
