exec(open('/home/ubuntu/pob-cli/find_tree_paths_fixed.py').read().split("for target")[0])
ind={x:{y for y in nodes[x]['adj'] if y in cur} for x in cur}
for x in sorted(cur,key=lambda z: len(ind[z])):
 if len(ind[x])<=1: print(x,nodes[x]['name'],'degree',len(ind[x]))
