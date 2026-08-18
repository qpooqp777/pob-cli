from pathlib import Path
import re, collections, xml.etree.ElementTree as ET
p=Path('/home/ubuntu/PathOfBuilding/src/TreeData/3_29/tree.lua').read_text(); starts=list(re.finditer(r'^\s*\[(\d+)\]\s*=\s*\{',p,re.M)); nodes={}
for i,m in enumerate(starts):
 end=starts[i+1].start() if i+1<len(starts) else len(p); b=p[m.end():end]; nid=m.group(1); nm=re.search(r'\["name"\]\s*=\s*"([^"]+)"',b); adj=set()
 for key in ['out','in']:
  for mm in re.finditer(r'\["'+key+r'"\]\s*=\s*\{(.*?)\}',b,re.S): adj.update(re.findall(r'"(\d+)"',mm.group(1)))
 nodes[nid]={'name':nm.group(1) if nm else '', 'adj':adj}
for nid,d in list(nodes.items()):
 for other in d['adj']:
  if other in nodes: nodes[other]['adj'].add(nid)
root=ET.parse('/home/ubuntu/pob-cli/attached_build.xml').getroot(); spec=root.find('.//Spec'); cur=set(re.sub(r'\s+','',spec.attrib['nodes']).split(',')); start='54447'
def reachable(skip):
 seen={start}; q=collections.deque([start])
 while q:
  x=q.popleft()
  for y in nodes.get(x,{}).get('adj',[]):
   if y!=skip and y not in seen: seen.add(y); q.append(y)
 return seen
for x in sorted(cur):
 if x==start: continue
 r=reachable(x)
 if cur-{x} <= r:
  print(x,nodes.get(x,{}).get('name'))
