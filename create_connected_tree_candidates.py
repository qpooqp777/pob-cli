from pathlib import Path
import re
base=Path('/home/ubuntu/pob-cli/attached_build.xml').read_text()
m=re.search(r'(<Spec[^>]*\bnodes=")([^"]+)("[^>]*>)',base); cur=m.group(2).replace('\n','').split(',')
paths={
 'path_breath_of_rime':['60170','21460'],
 'path_coldhearted':['4502','33783','3656','24050'],
 'path_trickery':['4502','33783','3656','20546','35894'],
 'path_doom_cast':['61653','36858','60405','25757','61981'],
 'path_snowforged':['4502','20852','6785','42649'],
}
for name,path in paths.items():
 nodes=cur[:]
 for x in path:
  if x not in nodes: nodes.append(x)
 text=base[:m.start(2)]+','.join(nodes)+base[m.end(2):]
 Path('/tmp/'+name+'.xml').write_text(text)
 print(name,[x for x in path if x not in cur])
