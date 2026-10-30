"""Resume the preparation after its original startup-marker assertion."""
from pathlib import Path
r=Path(__file__).resolve().parent.parent
d=r/'compat/sheng-graphics/v106'
source=(r/'tools/prepare_probe_v106.py').read_text()
start=source.index("p=d/'start-native-desktop-v106.sh'")
exec(compile(source[start:],str(r/'tools/prepare_probe_v106.py'),'exec'))
