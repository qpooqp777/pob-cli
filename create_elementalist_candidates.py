from pathlib import Path
base = Path('/home/ubuntu/pob-cli/attached_build.xml').read_text()
variants = {
    'amulet_cold_upgrade': base.replace('+95 to maximum Life\n', '+95 to maximum Life\n+1 to Level of all Cold Skill Gems\n+20% to Cold Damage over Time Multiplier\n', 1),
    'gloves_defence_upgrade': base.replace('+108 to maximum Life\n', '+108 to maximum Life\n+150 to maximum Energy Shield\n+100 to Armour\n', 1),
    'weapon_spell_upgrade': base.replace('31% increased Projectile Damage\n', '31% increased Projectile Damage\n+1 to Level of all Spell Skill Gems\n+60% to Cold Damage over Time Multiplier\n', 1),
}
for name, text in variants.items():
    if text == base:
        raise SystemExit(f'candidate not changed: {name}')
    Path(f'/tmp/{name}.xml').write_text(text)
    print(name)
