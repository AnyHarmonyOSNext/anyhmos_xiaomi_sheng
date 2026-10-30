from pathlib import Path
import struct, json, subprocess
base=Path.cwd(); out=base/'analysis'; src=Path('E:/SHENG_STOCK_303/images')
b=(src/'vendor_boot.img').read_bytes(); fields=struct.unpack_from('<8s5I2048sI16sIIQ4I',b)
keys=['magic','version','page_size','kernel_addr','ramdisk_addr','ramdisk_size','cmdline','tags_addr','name','header_size','dtb_size','dtb_addr','table_size','entry_num','entry_size','bootconfig_size']; data=dict(zip(keys,fields)); data={k:v.decode(errors='replace').rstrip('\x00') if isinstance(v,bytes) else v for k,v in data.items()}; print(json.dumps(data,indent=2)); (out/'vendor_header.json').write_text(json.dumps(data,indent=2))
a=lambda n:(n+4095)//4096*4096
rt=a(data['header_size']); tab=rt+a(data['ramdisk_size'])+a(data['dtb_size']); rows=[]
for i in range(data['entry_num']):
 pos=tab+i*data['entry_size']; size,offset,typ,name=struct.unpack_from('<III32s',b,pos); name=name.split(b'\0')[0].decode(); rows.append(dict(name=name,size=size,offset=offset,type=typ)); (base/'work'/'stock_vendor_boot'/f'fragment_{i}_{name}.lz4').write_bytes(b[rt+offset:rt+offset+size])
print(rows); (out/'vendor_fragments.json').write_text(json.dumps(rows,indent=2)); bc=tab+a(data['table_size']); (out/'vendor_bootconfig.txt').write_bytes(b[bc:bc+data['bootconfig_size']]); print(b[bc:bc+data['bootconfig_size']].decode(errors='replace'))
b=Path('C:/Users/YOUR_USER/Downloads/FastbootFlasher_Ver1.8_x64/images/boot.img').read_bytes(); print('huawei header @4096',b[4096:4224].hex()); print('ELF offset',b.find(b'\x7fELF'));print('fdt offset',b.find(bytes.fromhex('d00dfeed')))
for d in ['stock_init_boot','stock_boot']:
 b=(base/'work'/d/('kernel' if d=='stock_boot' else 'ramdisk.cpio')).read_bytes(); print(d)
 if d=='stock_boot':
  import re
  for v in re.findall(rb'Linux version [^\0\n]+',b): print(v.decode(errors='replace'))
