"""Recreate the real PAL stream after standby instead of reusing a silent handle."""
from pathlib import Path
import hashlib
import json
import subprocess

r = Path(__file__).resolve().parent.parent
d = r / 'compat/sheng-audio/lifecycle-v142'
d.mkdir(exist_ok=True)
source = r / 'compat/sheng-audio/pal-bridge-v1/audio_vdi.c'
s = source.read_text()
s = s.replace('int fd, running, muted;', 'int fd, running, muted, backend_open;')
start = s.index('static int start(struct IAudioRenderVdi *self)')
end = s.index('static int set_volume(', start)
s = s[:start] + '''/* Caller holds r->lock. A PAL stopped handle can accept writes while its
 * speaker route stays silent. Release that handle and open a fresh real stream.
 * Preserve the native sink object and its requested volume/mute state. */
static int open_backend(struct render *r)
{
    if (r->backend_open) return 0;
    struct sheng_pal_reply reply={0};
    int rc=sheng_pal_request(r->fd,SHENG_PAL_OPEN,48000,2,0,0,&reply);
    if (rc) return rc;
    r->backend_open=1;
    rc=command(r,SHENG_PAL_VOLUME,r->muted?0:(unsigned)(r->volume*1000000.0f));
    fprintf(stderr,"SHENG_AUDIO_BACKEND_REOPEN rc=%d volume=%.4f muted=%d\\n",rc,r->volume,r->muted);
    return rc;
}
static int stop_backend(struct render *r)
{
    if (!r->backend_open) { r->running=0; return 0; }
    int rc=command(r,SHENG_PAL_STOP,0);
    if (rc) return rc;
    r->running=0;
    rc=command(r,SHENG_PAL_CLOSE,0);
    if (!rc) r->backend_open=0;
    fprintf(stderr,"SHENG_AUDIO_BACKEND_RELEASE rc=%d\\n",rc);
    return rc;
}
static int start(struct IAudioRenderVdi *self)
{
    struct render *r=(void *)self; pthread_mutex_lock(&r->lock);
    int rc=open_backend(r);
    if (!rc) rc=command(r,SHENG_PAL_START,0);
    if (!rc) r->running=1;
    pthread_mutex_unlock(&r->lock); return rc;
}
static int stop(struct IAudioRenderVdi *self)
{
    struct render *r=(void *)self; pthread_mutex_lock(&r->lock);
    int rc=stop_backend(r);
    pthread_mutex_unlock(&r->lock); return rc;
}
static int pause_render(struct IAudioRenderVdi *self)
{
    return stop(self);
}
static int resume_render(struct IAudioRenderVdi *self)
{
    return start(self);
}
static int flush(struct IAudioRenderVdi *self)
{
    struct render *r=(void *)self; pthread_mutex_lock(&r->lock);
    int was_running=r->running, rc=stop_backend(r);
    if (!rc) rc=open_backend(r);
    if (!rc && was_running) rc=command(r,SHENG_PAL_START,0);
    if (!rc) r->running=was_running;
    pthread_mutex_unlock(&r->lock); return rc;
}
''' + s[end:]
# A suspended sink has no hardware stream; keep the requested volume locally.
s = s.replace('int rc=command(r,SHENG_PAL_VOLUME,r->muted?0:(unsigned)(volume*1000000.0f));',
              'int rc=r->backend_open?command(r,SHENG_PAL_VOLUME,r->muted?0:(unsigned)(volume*1000000.0f)):0;')
s = s.replace('int rc=command(r,SHENG_PAL_VOLUME,mute?0:(unsigned)(r->volume*1000000.0f));',
              'int rc=r->backend_open?command(r,SHENG_PAL_VOLUME,mute?0:(unsigned)(r->volume*1000000.0f)):0;')
s = s.replace('r->attrs=*attrs; r->volume=0.03f;', 'r->attrs=*attrs; r->volume=0.03f; r->backend_open=1;')
s = s.replace('int rc=command(r,SHENG_PAL_CLOSE,0); close(r->fd); r->fd=-1;',
              'int rc=r->backend_open?command(r,SHENG_PAL_CLOSE,0):0; close(r->fd); r->fd=-1;')
assert s != source.read_text()
(d / 'audio_vdi.c').write_text(s, newline='\n')
wslroot = '/mnt/c/' + str(r).replace('\\', '/').split(':/', 1)[1]
sdk = '/root/hmos-work/sdk-6.0.0.47/installed/native/llvm/bin/clang'
rel = 'compat/sheng-audio/lifecycle-v142'
cmd = (f'cd "{wslroot}" && {sdk} --target=aarch64-linux-ohos -D_GNU_SOURCE '
       '-O2 -Wall -Wextra -Werror -fPIC -shared '
       '-Icompat/sheng-audio/pal-bridge-v1 -Icompat/sheng-audio/pal-bridge-v1/include '
       f'{rel}/audio_vdi.c compat/sheng-audio/pal-bridge-v1/pal_client.c '
       f'-pthread -Wl,-z,defs -Wl,-soname,libsheng_audio_vdi.so -o {rel}/libsheng_audio_vdi.so')
subprocess.run(['wsl.exe', '-d', 'Ubuntu-22.04', '--', 'bash', '-lc', cmd], check=True)
p = d / 'libsheng_audio_vdi.so'
v = dict(version='v142', stage='built_not_tested', bytes=p.stat().st_size,
         sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
         scope='real PAL stream release and recreation on standby, volume/mute preserved',
         hardware_volume_unchanged=True, unsupported_mmap_and_latency_unchanged=True,
         persistent=False, repeated_playback_verified=False)
(d / 'manifest.json').write_text(json.dumps(v, indent=2) + '\n')
print(json.dumps(v, indent=2))
