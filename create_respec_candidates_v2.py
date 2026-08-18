from pathlib import Path
import re
base=Path('/home/ubuntu/pob-cli/attached_build.xml').read_text(); m=re.search(r'(<Spec[^>]*\bnodes=")([^"]+)("[^>]*>)',base); cur=m.group(2).replace('\n','').split(',')
removals=['11689','19008','43061','14745']
paths={'respec_v2_doom_cast':['61653','36858','60405','25757','61981'],'respec_v2_snowforged':['4502','20852','6785','42649'],'respec_v2_coldhearted_trickery':['4502','33783','3656','20546','35894']}
for name,path in paths.items():
 add=[x for x in path if x not in cur]; remove=removals[:len(add)]; nodes=[x for x in cur if x not in remove]
 for x in path:
  if x not in nodes: nodes.append(x)
 Path('/tmp/'+name+'.xml').write_text(base[:m.start(2)]+','.join(nodes)+base[m.end(2):]); print(name,'remove',remove,'add',add)
