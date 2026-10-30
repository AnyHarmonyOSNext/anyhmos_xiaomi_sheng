"""Read-only CRC and source-hash check of original vendor_dlkm GPU modules."""
from pathlib import Path
import struct,json,hashlib
root=Path(__file__).resolve().parent.parent
expected={line.split()[1]:int(line.split()[0],16) for line in (root/'analysis/gki-sheng-exports.symvers').read_text().splitlines()}
original=json.loads((root/'analysis/stock-module-import-crcs.json').read_text())['symbols']
reports=[]
for name in ['gpucc-kalama','msm_performance','qcom_va_minidump','coresight','msm_kgsl']:
    path=root/f'work/stock_gpu_modules/vendor_dlkm/lib/modules/{name}.ko'
    b=path.read_bytes();assert b[:6]==b'\x7fELF\x02\x01'
    official=root/f'work/official303_vendor_dlkm/vendor_dlkm/lib/modules/{name}.ko'
    assert official.read_bytes()==b,('Different from official 303 module',name)
    offset=struct.unpack_from('<Q',b,40)[0];size,count,strings=struct.unpack_from('<HHH',b,58)
    sections=[struct.unpack_from('<IIQQQQIIQQ',b,offset+i*size) for i in range(count)]
    s=sections[strings];names=b[s[4]:s[4]+s[5]];versions={};info={}
    for s in sections:
        section=names[s[0]:].split(b'\0',1)[0];data=b[s[4]:s[4]+s[5]]
        if section==b'.modinfo':
            for word in data.split(b'\0'):
                if b'=' in word:
                    k,v=word.split(b'=',1);info[k.decode()]=v.decode()
        if section==b'__versions':
            assert len(data)%64==0
            for i in range(0,len(data),64):versions[data[i+8:i+64].split(b'\0',1)[0].decode()]=struct.unpack_from('<Q',data,i)[0]
    mismatches={k:[hex(v),hex(expected[k])] for k,v in versions.items() if k in expected and v!=expected[k]}
    old_mismatches={k:[hex(v),original[k]] for k,v in versions.items() if k in original and v!=int(original[k],16)}
    assert not mismatches and not old_mismatches,(name,mismatches,old_mismatches)
    # The actual 303 vendor ramdisk also retains 5.15.78. In this exact kernel,
    # same_magic(has_crcs) compares the suffix after the first space; CRCs and
    # module_layout remain checked. No force-load or vermagic edits are used.
    assert info['vermagic'].partition(' ')[2]=='SMP preempt mod_unload modversions aarch64',info
    assert versions['module_layout']==expected['module_layout']
    reports.append({'module':name,'sha256':hashlib.sha256(b).hexdigest(),'official303_identical':True,'imports':len(versions),'matched_kernel':sum(k in expected for k in versions),'other_vendor_imports':[k for k in versions if k not in expected],'cfi_symbol_present':b'__cfi_check\0' in b,'info':info})
(root/'analysis/stock-gpu-abi-verification.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps([{k:v for k,v in item.items() if k!='info'} for item in reports],indent=2))
