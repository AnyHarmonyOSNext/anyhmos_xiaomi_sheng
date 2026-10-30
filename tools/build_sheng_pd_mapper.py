"""Build a static PD mapper for exact original, uncompressed Sheng descriptors.

Run with WSL Python. Reference repositories remain untouched. QMI encoding and
the response data come from upstream and the original firmware respectively.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

r = Path(__file__).resolve().parent.parent
out = r / 'compat/sheng-audio/pd-mapper-v1'
src = out / 'src'
src.mkdir(parents=True, exist_ok=True)
refs = {
    'pd-mapper': '5ecd2fe926aca7abfe40724177f63b942cff3947',
    'qrtr': '29e36ae164389580a0f8ea7a7fdb728140ae978d',
}
for repo, commit in refs.items():
    p = Path('/root/hmos-reference') / repo
    actual = subprocess.check_output(['git', '-C', str(p), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == commit, (repo, actual)
    shutil.copy2(p / 'LICENSE', out / (repo + '-LICENSE'))

pd = Path('/root/hmos-reference/pd-mapper')
qr = Path('/root/hmos-reference/qrtr')
for name in ['pd-mapper.c', 'assoc.c', 'assoc.h', 'json.c', 'json.h', 'servreg_loc.c', 'servreg_loc.h']:
    shutil.copy2(pd / name, src / name)
for p in (qr / 'include').glob('*.h'):
    shutil.copy2(p, src / p.name)
for name in ['qrtr.c', 'qmi.c', 'logging.c']:
    shutil.copy2(qr / 'lib' / name, src / name)

p = src / 'json.c'
s = p.read_text().replace('#include <lzma.h>\n', '')
s = s.replace('extern int lzma_decomp(const char *file);', '')
old = '''\tif ((strlen(file) > 3) && !strcmp(&file[strlen(file)-3], ".xz"))
\t        fd = lzma_decomp(file);
\telse
\t        fd = open(file, O_RDONLY);'''
assert s.count(old) == 1
s = s.replace(old, '''\t/* Original Sheng descriptors are plain .jsn; never pretend to decode XZ. */
\tif ((strlen(file) > 3) && !strcmp(&file[strlen(file)-3], ".xz")) {
\t\terrno = ENOTSUP;
\t\treturn NULL;
\t}
\tfd = open(file, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);''')
p.write_text(s)

p = src / 'pd-mapper.c'
s = p.read_text()
s = s.replace('static struct pd_map *pd_maps;', 'static struct pd_map *pd_maps;\nstatic const char *map_directory;')
begin = s.index('static int concat_path(')
end = s.index('static int pd_load_maps(', begin)
s = s[:begin] + '''/* Local integration: scan only the explicitly staged original descriptors. */
static int pd_enumerate_jsons(struct assoc *json_set)
{
    struct dirent *de;
    char path[PATH_MAX];
    DIR *dir = opendir(map_directory);
    int count = 0;
    if (!dir) return -1;
    while ((de = readdir(dir))) {
        size_t n = strlen(de->d_name);
        if (n <= 4 || strcmp(de->d_name + n - 4, ".jsn")) continue;
        if (snprintf(path, sizeof(path), "%s/%s", map_directory, de->d_name) >= (int)sizeof(path)) {
            closedir(dir); return -1;
        }
        struct stat st;
        if (lstat(path, &st) || !S_ISREG(st.st_mode) || st.st_size <= 0 || st.st_size > 65536) {
            closedir(dir); return -1;
        }
        assoc_set(json_set, path, NULL);
        count++;
    }
    closedir(dir);
    printf("PD_DESCRIPTOR_FILES=%d\\n", count);
    return count ? 0 : -1;
}

''' + s[end:]
s = s.replace('\tpd_enumerate_jsons(&json_set);', '\tif (pd_enumerate_jsons(&json_set) < 0) { assoc_destroy(&json_set); return -1; }')
s = s.replace('unsigned int txn;', 'unsigned int txn = 0;')
s = s.replace('DEFINE_QRTR_PACKET(resp_buf, 256);', 'DEFINE_QRTR_PACKET(resp_buf, 4096);')
s = s.replace('\t\t\tentry = &resp.domain_list[resp.domain_list_len++];', '''\t\t\tif (resp.domain_list_len >= 255 || strlen(pd_map->domain) >= sizeof(resp.domain_list[0].name)) {
\t\t\t\tresp.result.result = QMI_RESULT_FAILURE; resp.result.error = QMI_ERR_INTERNAL;
\t\t\t\tresp.domain_list_len = 0; goto respond;
\t\t\t}
\t\t\tentry = &resp.domain_list[resp.domain_list_len++];''')
s = s.replace('\treq.name[sizeof(req.name)-1]', '\tprintf("PD_LOOKUP_REQUEST=%s\\n", req.name);\n\treq.name[sizeof(req.name)-1]')
# Terminate before logging malformed remote strings.
s = s.replace('\tprintf("PD_LOOKUP_REQUEST=%s\\n", req.name);\n\treq.name[sizeof(req.name)-1] = \'\\0\';', '\treq.name[sizeof(req.name)-1] = \'\\0\';\n\tprintf("PD_LOOKUP_REQUEST=%s\\n", req.name);')
s = s.replace('\tsr_domain = json_get_child(root, "sr_domain");', '\tsr_domain = json_get_child(root, "sr_domain");\n\tif (!sr_domain) { json_free(root); return -1; }')
s = s.replace('\tsr_service = json_get_child(root, "sr_service");', '\tsr_service = json_get_child(root, "sr_service");\n\tif (!sr_service) { json_free(root); return -1; }')
s = s.replace('\t\tmap->instance = number;', '\t\tmap->instance = number;\n\t\tprintf("PD_MAP service=%s domain=%s instance=%d\\n", map->service, map->domain, map->instance);')
s = s.replace('\tret = pd_load_maps();', '''\tsetvbuf(stdout, NULL, _IOLBF, 0);
\tif ((argc != 3 && argc != 4) || strcmp(argv[1], "--maps-dir") || argv[2][0] != '/' ||
\t    (argc == 4 && strcmp(argv[3], "--validate"))) {
\t\tfprintf(stderr, "usage: pd-mapper --maps-dir /absolute/directory [--validate]\\n"); return 2;
\t}
\tmap_directory = argv[2];
\tret = pd_load_maps();''')
s = s.replace('\tfd = qrtr_open(0);', '\tif (argc == 4) { puts("PD_MAP_VALIDATION_OK=1"); return 0; }\n\tfd = qrtr_open(0);')
s = s.replace('\tfor (;;) {\n\t\tret = qrtr_poll', '\tputs("PD_LOCATOR_PUBLISHED=64:257:0");\n\tfor (;;) {\n\t\tret = qrtr_poll')
p.write_text(s)

sdk = Path('/root/hmos-work/sdk-6.0.0.47/installed/native')
(src / 'linux').mkdir(exist_ok=True)
header = (sdk / 'sysroot/usr/include/linux/qrtr.h').read_text()
# The generated SDK Linux socket header duplicates musl sockaddr_storage.
# Only select the libc family typedef; preserve the kernel QRTR wire layout.
header = header.replace('#include <linux/socket.h>', '#include <sys/socket.h>')
header = header.replace('__kernel_sa_family_t sq_family;', 'sa_family_t sq_family;')
header = header.replace('} __packed;', '} __attribute__((packed));')
(src / 'linux/qrtr.h').write_text(header)
cc = [str(sdk / 'llvm/bin/clang'), '--target=aarch64-linux-ohos',
      '--sysroot=' + str(sdk / 'sysroot'), '-static', '-Oz', '-Wall',
      '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections', '-I' + str(src)]
sources = ['pd-mapper.c', 'assoc.c', 'json.c', 'servreg_loc.c', 'qrtr.c', 'qmi.c', 'logging.c']
subprocess.run(cc + [str(src / p) for p in sources] + ['-o', str(out / 'sheng-pd-mapper')], check=True)
subprocess.run([str(sdk / 'llvm/bin/llvm-strip'), str(out / 'sheng-pd-mapper')], check=True)
files = [p for p in out.rglob('*') if p.is_file() and p.name != 'manifest.json']
manifest = dict(upstream=refs, maps='Original modem_a image/*.jsn, copied and SHA-checked in RAM',
                scope='Plain JSON only, original QMI locator; does not synthesize DSP service state',
                files={str(p.relative_to(out)): dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files})
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest['files']['sheng-pd-mapper']))
