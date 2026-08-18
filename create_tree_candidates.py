from pathlib import Path
import re
base = Path('/home/ubuntu/pob-cli/attached_build.xml').read_text()
m = re.search(r'(<Spec[^>]*\bnodes=")([^"]+)("[^>]*>)', base)
if not m: raise SystemExit('Spec nodes not found')
current = m.group(2).replace('\n','').split(',')
current = [x for x in current if x]
variants = {
    'add_coldhearted': ['24050'],
    'add_trickery': ['35894'],
    'add_doom_cast': ['61981'],
    'add_breath_of_rime': ['21460'],
    'add_whispers_of_doom': ['22535'],
    'add_coldhearted_trickery': ['24050','35894'],
}
for name, additions in variants.items():
    nodes = current[:]
    for node in additions:
        if node not in nodes: nodes.append(node)
    text = base[:m.start(2)] + ','.join(nodes) + base[m.end(2):]
    Path('/tmp/'+name+'.xml').write_text(text)
    print(name, 'added', additions)
