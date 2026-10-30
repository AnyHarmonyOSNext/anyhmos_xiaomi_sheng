"""Run in WSL after the ABI build; fail on any stock symbol CRC mismatch."""
from pathlib import Path
import json

workspace = Path(__file__).resolve().parent.parent
out = Path('/root/hmos-work/gki-out-stock')
stock = json.loads((workspace/'analysis/stock-module-import-crcs.json').read_text())['symbols']
built = {}
for line in (out/'vmlinux.symvers').read_text().splitlines():
    fields = line.split()
    if len(fields) >= 2:
        built[fields[1]] = int(fields[0], 16)
common = sorted(stock.keys() & built.keys())
missing = sorted(stock.keys() - built.keys())
mismatches = {name: {'stock': stock[name], 'built': f'0x{built[name]:08x}'}
              for name in common if int(stock[name], 16) != built[name]}
report = {'compared_symbols': len(common), 'mismatches': mismatches,
          'not_in_vmlinux': missing, 'module_layout_stock': stock['module_layout'],
          'module_layout_built': f"0x{built.get('module_layout', 0):08x}",
          'scope': 'CRC match covers only observed stock imports; CFI and real device validation remain required'}
(workspace/'analysis/stock-gki-abi-comparison.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k,v in report.items() if k != 'not_in_vmlinux'}, indent=2))
print(f'{len(missing)} imports absent from vmlinux (including vendor-module exports)')
assert len(common) > 2000 and not mismatches
assert built.get('module_layout') == int(stock['module_layout'], 16)
