from pathlib import Path
base = Path('/home/ubuntu/pob-cli/slammerlappen_pob.xml').read_text()
variants = {
    'warcry_recovery': base.replace('{8460,60034}', '{8460,23021}'),
    'warcry_debilitate': base.replace('{8460,60034}', '{8460,12916}'),
    'charge_damage': base.replace('{4707,29652}', '{4707,40307}'),
}
for name, text in variants.items():
    Path(f'/tmp/{name}.xml').write_text(text)
    print(name, text != base)
