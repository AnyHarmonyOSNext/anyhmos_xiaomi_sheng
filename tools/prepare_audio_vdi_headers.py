"""Preserve public VDI headers and apply measured donor6.1 layout additions."""
from pathlib import Path
import hashlib
import json

r=Path(__file__).resolve().parent.parent
src=Path('/root/hmos-work/graphics-deps/source/drivers_peripheral/audio/interfaces/sound/v1_0')
dest=r/'compat/sheng-audio/pal-bridge-v1/include'
dest.mkdir(exist_ok=True)
report=[]
for p in sorted(src.glob('*.h')):
    text=p.read_text()
    if p.name=='iaudio_render_vdi.h':
        anchor='    int32_t (*GetVolume)(struct IAudioRenderVdi *self, float *volume);'
        assert text.count(anchor)==1
        text=text.replace(anchor,
            '    /* Donor6.1 wrapper: measured indirect call at 0x1a324, offset120. */\n'
            '    int32_t (*SetVolumeWithRamp)(struct IAudioRenderVdi *self, float volume, uint32_t duration);\n'+anchor)
    if p.name=='audio_types_vdi.h':
        anchor='    struct EcSampleAttributesVdi ecSampleAttributes;'
        assert text.count(anchor)==1
        text=text.replace(anchor,anchor+'\n    /* Donor converter copies through offset160 inclusive. */\n'
            '    uint32_t donorEcExtension[2];\n    uint64_t donorEcLayout;')
    if p.name=='iaudio_adapter_vdi.h':
        # Donor replaces public slot128 observer with five additional functions.
        start=text.index('    int32_t (*RegExtraParamObserver)')
        end=text.index('\n};',start)
        text=text[:start]+('    /* Unsupported donor-only adapter extensions at offsets128..168. */\n'
            '    int32_t (*donorExtensions[6])(void *, ...);')+text[end:]
    (dest/p.name).write_text(text)
    report.append(dict(name=p.name,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                       adapted_sha256=hashlib.sha256(text.encode()).hexdigest()))
(r/'analysis/audio-vdi-headers.json').write_text(json.dumps(report,indent=2)+'\n')
print('Prepared',len(report),'VDI headers; donor call evidence in analysis/donor-audio-vdi-indirect-calls.txt')
