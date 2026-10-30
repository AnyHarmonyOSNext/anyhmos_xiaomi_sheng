"""Focused inspection of pinned public signatures and donor ABI (WSL)."""
from pathlib import Path
import re,subprocess,json
base=Path('/root/hmos-work/graphics-deps')
source=base/'source/drivers_interface/display'
for name in ['composer/v1_0/include/idisplay_composer_interface.h','buffer/v1_0/include/idisplay_buffer.h']:
    text=(source/name).read_text()
    text=re.sub(r'/\*.*?\*/','',text,flags=re.S)
    print(name, text)
sdk=Path(json.loads(Path('/root/hmos-work/sdk-6.0.0.47/installation.json').read_text())['sdk'])
work=Path('/mnt/c/SHENG_WORKSPACE/work/donor-hdi-link')
for file in work.glob('*hdi_impl*'):
    result=subprocess.check_output([str(sdk/'llvm/bin/llvm-nm'),'-D','-C',str(file)],text=True)
    print(file.name)
    print('\n'.join(line for line in result.splitlines() if '::Get(' in line))
