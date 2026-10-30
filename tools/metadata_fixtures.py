from pathlib import Path
from lp_inspect import Sparse
for name,p in [('hmos','C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/hmos/super.img'),('stock','E:/SHENG_STOCK_303/images/super.img')]:
 s=Sparse(p);Path(f'analysis/{name}_super_metadata.raw').write_bytes(s.read(0,12288+65536*6))
