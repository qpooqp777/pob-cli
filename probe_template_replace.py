from pathlib import Path
import xml.etree.ElementTree as ET
src = Path('/home/ubuntu/pob-cli/attached_build.xml')
out = Path('/tmp/probe_toxic_template.xml')
root = ET.parse(src).getroot()
b = root.find('Build')
b.attrib.update({'className':'Ranger','ascendClassName':'Pathfinder','level':'80','label':'Toxic Rain Probe','targetVersion':'3_0'})
spec = root.find('Tree/Spec')
spec.attrib.update({'classId':'2','ascendClassId':'3','treeVersion':'3_29','nodes':'16236,59766,9864'})
first = root.find('Skills/SkillSet/Skill')
for child in list(first): first.remove(child)
meta = [
 ('ToxicRain','ToxicRain','Metadata/Items/Gems/SkillGemToxicRain','Toxic Rain'),
 ('SupportViciousProjectiles','SupportViciousProjectiles','Metadata/Items/Gems/SupportGemPhysicalProjectileAttackDamage','Vicious Projectiles'),
 ('SupportVoidManipulation','SupportVoidManipulation','Metadata/Items/Gems/SupportGemVoidManipulation','Void Manipulation'),
 ('SupportSwiftAffliction','SupportSwiftAffliction','Metadata/Items/Gems/SupportGemRapidDecay','Swift Affliction'),
 ('SupportMirageArcher','SupportMirageArcher','Metadata/Items/Gems/SupportGemMirageArcher','Mirage Archer'),
]
for skill, variant, gemid, name in meta:
    ET.SubElement(first,'Gem',{'skillId':skill,'variantId':variant,'gemId':gemid,'nameSpec':name,'level':'20','quality':'20','enabled':'true','enableGlobal1':'true','enableGlobal2':'true','count':'nil'})
ET.indent(root, space='\t')
out.write_text(ET.tostring(root, encoding='unicode')+'\n', encoding='utf-8')
print(out)
