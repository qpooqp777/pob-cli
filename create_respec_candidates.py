from pathlib import Path
import re
base=Path('/home/ubuntu/pob-cli/attached_build.xml').read_text()
m=re.search(r'(<Spec[^>]*\bnodes=")([^"]+)("[^>]*>)',base); cur=m.group(2).replace('\n','').split(',')
# These are current terminal branches selected for comparison; each candidate spends the same number of points.
removals=['9586','57197','61308','14745']
paths={
 'respec_doom_cast':['61653','36858','60405','25757','61981'],
 'respec_snowforged':['4502','20852','6785','42649'],
 'respec_coldhearted_trickery':['4502','33783','3656','20546','35894'],
}
for name,path in paths.items():
    add=[x for x in path if x not in cur]
    remove=removals[:len(add)]
    nodes=[x for x in cur if x not in remove]
    for x in path:
        if x not in nodes: nodes.append(x)
    text=base[:m.start(2)]+','.join(nodes)+base[m.end(2):]
    Path('/tmp/'+name+'.xml').write_text(text)
    print(name,'remove',remove,'add',add)
