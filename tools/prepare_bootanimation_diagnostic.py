"""Explicit test fixture for original picture player, never a desktop screenshot."""
from pathlib import Path
from PIL import Image, ImageDraw
import io,zipfile,json,hashlib
r=Path(__file__).resolve().parent.parent
p=r/'compat/sheng-graphics/bootanimation-diagnostic-v1';p.mkdir(exist_ok=True)
z=p/'bootpic.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
 out.writestr('config.json',json.dumps({'FrameRate':30}))
 for n in range(300):
  im=Image.new('RGB',(64,64),(12,25,50));d=ImageDraw.Draw(im)
  d.rectangle((1,1,62,62),outline=(255,255,0),width=2)
  d.rectangle((4,14,30,49),fill=(0,190,230))
  d.rectangle((33,14,59,49),fill=(240,40,130))
  d.rectangle((4+n%48,52,11+n%48,58),fill=(255,255,255))
  stream=io.BytesIO();im.save(stream,format='PNG')
  out.writestr(f'{n:04}.png',stream.getvalue())
report={'path':str(z.relative_to(r)),'bytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'frames':300,'fps':30,'status':'offline synthetic diagnostic asset for original boot picture player; not a system screenshot'}
(p/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
