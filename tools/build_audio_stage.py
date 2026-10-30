"""Merge individually ABI-verified official module plans, preserving dependency order."""
from pathlib import Path
import json
r=Path(__file__).resolve().parent.parent
stages={
    'transport':['adsp_loader_dlkm','q6_dlkm'],
    'card':['pinctrl_lpi_dlkm','stub_dlkm','lpass_cdc_va_macro_dlkm','lpass_cdc_wsa_macro_dlkm',
            'lpass_cdc_wsa2_macro_dlkm','swr_haptics_dlkm','hdmi_dlkm','cs35l43_dlkm','machine_dlkm'],
}
for stage,targets in stages.items():
    entries={}
    for target in targets:
        plan=json.loads((r/'analysis'/f'official303-{target}-module-plan.json').read_text())
        for e in plan:
            if e['file'] in entries:assert entries[e['file']]==e
            else:entries[e['file']]=e
    lines=['#!/busybox sh','set -eu','B=/busybox','R=/hmos-root','M=$R/vendor_dlkm/lib/modules',
           '[ "$($B uname -r)" = 5.15.178-android13-8-00021-g6f2f96be86b9-ab13729987 ] || exit 30',
           f'echo AUDIO_{stage.upper()}_BEGIN=1']
    for e in entries.values():
        assert e['cfi_present'] and e['module_load_flags']==0
        lines += [f"if ! $B grep -q '^{e['name']} ' /proc/modules; then",
                  f" echo '{e['sha256']}  '$M/{e['file']} | $B sha256sum -c -",
                  f" echo AUDIO_MODULE_BEGIN={e['file']}",
                  f" $B timeout 12 $B insmod $M/{e['file']}",
                  f" $B grep '^{e['name']} ' /proc/modules",'fi']
    lines += [f'echo AUDIO_{stage.upper()}_COMPLETE=1']
    (r/'output'/f'load-official303-audio-{stage}.sh').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    (r/'analysis'/f'official303-audio-{stage}-plan.json').write_text(json.dumps(list(entries.values()),indent=2)+'\n')
    print(stage,len(entries))
