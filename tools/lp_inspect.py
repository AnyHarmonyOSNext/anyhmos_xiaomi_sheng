from pathlib import Path
import struct,json
class Sparse:
 def __init__(self,p):
  self.f=open(p,'rb'); b=self.f.read(28); self.ext=[]
  if b[:4]!=bytes.fromhex('3aff26ed'): self.ext=[(0,Path(p).stat().st_size,0,0xcac1)]; return
  _,_,_,fh,ch,bs,blocks,n,_=struct.unpack('<I4H4I',b); self.f.seek(fh); pos=0
  for _ in range(n):
   hd=self.f.read(ch); typ,_,nb,total=struct.unpack_from('<2H2I',hd); off=self.f.tell(); self.ext.append((pos,pos+nb*bs,off,typ));pos+=nb*bs;self.f.seek(off+total-ch)
 def read(self,off,n):
  out=b''
  for st,en,fp,typ in self.ext:
   if st>=off+n: break
   if en<=off: continue
   a=max(st,off);z=min(en,off+n)-a
   if typ==0xcac1:self.f.seek(fp+a-st);out+=self.f.read(z)
   elif typ==0xcac2:self.f.seek(fp);v=self.f.read(4);out+=(v*((z+7)//4))[(a-st)%4:(a-st)%4+z]
   else:out+=bytes(z)
  if len(out)!=n:raise ValueError((off,n,len(out)))
  return out

def parse(p):
 s=Sparse(p);g=s.read(4096,52);magic,sz,checksum,maxsize,slots,lbs=struct.unpack('<II32sIII',g); print('GEOMETRY',hex(magic),maxsize,slots,lbs)
 b=s.read(12288,maxsize);magic,maj,minor,hs,hsha,ts,tsha=struct.unpack_from('<IHHI32sI32s',b);tables=b[hs:hs+ts];print('HEADER',hex(magic),maj,minor,hs,ts);res={'path':str(p),'geometry':dict(metadata_max_size=maxsize,slots=slots,block_size=lbs),'partitions':[],'extents':[],'groups':[],'block_devices':[]}
 for key,pos,fmt in [('partitions',80,'<36sIIII'),('extents',92,'<QIQI'),('groups',104,'<36sIQ'),('block_devices',116,'<QIIQ36sI')]:
  off,num,entry=struct.unpack_from('<III',b,pos)
  for i in range(num):
   v=struct.unpack_from(fmt,tables,off+i*entry);v=[x.split(b'\0')[0].decode() if isinstance(x,bytes) else x for x in v];res[key].append(v)
 print(json.dumps(res,ensure_ascii=False,indent=2));return res
if __name__=='__main__':
 for name,p in [('hmos','C:/MIO-KITCHEN-PYSIDE6-5.0.0-PREVIEW/hmos/super.img'),('stock','E:/SHENG_STOCK_303/images/super.img')]:
  r=parse(p);Path('analysis',name+'_super_metadata.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
