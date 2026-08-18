from pathlib import Path
base = Path('/home/ubuntu/pob-cli/slammerlappen_pob.xml').read_text()
needle = '+28% to Cold Resistance\n'
replacement = needle + '+30% to Chaos Resistance\n'
assert base.count(needle) == 1
candidate = base.replace(needle, replacement)
Path('/tmp/body_chaos.xml').write_text(candidate)
