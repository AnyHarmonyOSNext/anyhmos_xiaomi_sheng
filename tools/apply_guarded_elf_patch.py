"""Apply reviewed byte patches to a new ELF copy, with whole-file SHA guards."""
from pathlib import Path
import argparse,hashlib,json,os,stat

def digest(data):return hashlib.sha256(data).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--manifest',type=Path,required=True)
 ap.add_argument('--input',type=Path,required=True)
 ap.add_argument('--output',type=Path,required=True)
 args=ap.parse_args()
 source=args.input.resolve(strict=True);output=args.output.resolve()
 if source==output:raise ValueError('Input and output must be different; preserve original ELF')
 if output.exists():raise FileExistsError(output)
 spec=json.loads(args.manifest.read_text(encoding='utf-8'));raw=source.read_bytes()
 if raw[:6]!=b'\x7fELF\x02\x01':raise ValueError('Expected little-endian ELF64')
 if digest(raw)!=spec['input_sha256']:raise ValueError('Input SHA mismatch; unsupported donor build')
 for guard in spec.get('guards',[]):
  offset=guard['offset'];expected=bytes.fromhex(guard['bytes'])
  if offset<0 or raw[offset:offset+len(expected)]!=expected:raise ValueError(f'Guard mismatch at {offset}')
 result=bytearray(raw);occupied=set()
 for change in spec['changes']:
  offset=change['offset'];before=bytes.fromhex(change['before']);after=bytes.fromhex(change['after'])
  if not before or len(before)!=len(after) or offset<0 or offset+len(before)>len(raw):raise ValueError('Invalid patch bounds/size')
  if raw[offset:offset+len(before)]!=before:raise ValueError(f'Before bytes mismatch at {offset}')
  region=set(range(offset,offset+len(before)))
  if occupied.intersection(region):raise ValueError('Overlapping changes')
  occupied.update(region);result[offset:offset+len(after)]=after
 if digest(result)!=spec['output_sha256']:raise ValueError('Output SHA mismatch; no file created')
 with output.open('xb') as file:file.write(result)
 os.chmod(output,stat.S_IMODE(source.stat().st_mode))
 print(json.dumps({'output':str(output),'bytes':len(result),'sha256':digest(result),'module':spec['name']},ensure_ascii=False))
if __name__=='__main__':main()
