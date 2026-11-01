"""Apply reviewed GEM-W00 SP12 recipes to the known sheng vendor ramdisk.

Only host files are written. Proprietary input/output binaries stay outside Git.
Recipe evidence is static; this does not certify a successful device boot.
"""

import argparse
import difflib
import gzip
import hashlib
import io
import json
import pathlib
import re
import struct
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--donor', type=pathlib.Path, required=True)
parser.add_argument('--original', type=pathlib.Path, required=True)
parser.add_argument('--tools', type=pathlib.Path, required=True)
parser.add_argument('--work', type=pathlib.Path)
parser.add_argument('--composer', type=pathlib.Path)
parser.add_argument('--composer-sha256')
parser.add_argument('--present-fence-bridge', action='store_true')
parser.add_argument('--refresh-helper', type=pathlib.Path)
parser.add_argument('--refresh-helper-sha256')
parser.add_argument(
    '--recipe-dir', type=pathlib.Path, default=REPO / 'patches/donor/gem-w00-111-sp12'
)
parser.add_argument(
    '--regional-resources',
    dest='experimental_regional_resources',
    action=argparse.BooleanOptionalAction,
    default=True,
    help='Select verified GEM-W00 China resource layers; use --no-regional-resources for baseline comparison',
)
args = parser.parse_args()
if bool(args.composer) != bool(args.composer_sha256):
    parser.error('--composer and --composer-sha256 must be supplied together')
if args.present_fence_bridge and not args.composer:
    parser.error('Present fence bridge requires a matching custom composer')
if bool(args.refresh_helper) != bool(args.refresh_helper_sha256) or (
    args.refresh_helper and not args.composer
):
    parser.error('Refresh helper requires its hash and a custom composer')
sys.path.insert(0, str(args.tools / 'python-libs'))
sys.path.insert(0, str(REPO / 'tools'))
from elftools.elf.elffile import ELFFile
import vendor_ramdisk_edit as vr
from build_promax_images import cygpath
from patch_refresh_policy import INPUT_SHA256, patch_policy

ROOT = args.donor
WORK = args.work or ROOT / 'port-work'
WORK.mkdir(parents=True, exist_ok=True)
P = 'sheng-compat-v118/'
G = P + 'graphics/'
base = args.original / 'images/vendor_boot.img'
expected_base = '6fd2ed9de8442a8c1301d8e8c3835a1bdf83ca145f25375491ba56e84b9fc615'
assert hashlib.sha256(base.read_bytes()).hexdigest() == expected_base
vr.MAGISKBOOT = str(args.tools / 'android-fs/magiskboot.exe')
container = base.read_bytes()
page = struct.unpack_from('<I', container, 12)[0]
header_size = struct.unpack_from('<I', container, 2096)[0]
ramdisk_size = struct.unpack_from('<I', container, 24)[0]
ramdisk_offset = (header_size + page - 1) // page * page
(WORK / 'base.lz4').write_bytes(container[ramdisk_offset : ramdisk_offset + ramdisk_size])
subprocess.run(
    [vr.MAGISKBOOT, 'decompress', str(WORK / 'base.lz4'), str(WORK / 'base.cpio')],
    check=True,
    capture_output=True,
)


# 仅提取索引中存在的供体普通文件
def extract_guard(path, previous=False):
    if not previous:
        part = path.split('/')[1]
        records = json.loads((ROOT / 'metadata' / f'{part}-files.json').read_text(encoding='utf-8'))
        relative = path if part == 'system' else '/' + path.split('/', 2)[2]
        record = next((x for x in records if x['path'] == relative), None)
        if record is None or record['type'] != 'FILE':
            raise ValueError('Guard input must be an indexed regular donor file: ' + path)
    destination = (
        ROOT
        / ('metadata/old-guard-inputs' if previous else 'metadata/guard-inputs')
        / path.lstrip('/')
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    partition = path.split('/')[1]
    image = (
        args.original / 'images/super.img'
        if previous
        else ROOT / 'extracted/base' / f'{partition}.img'
    )
    relative = path if partition == 'system' else '/' + path.split('/', 2)[2]
    command = (
        [str(args.tools / 'erofs-cygwin/dump.erofs.exe')]
        + (['--offset=996147200'] if previous else [])
        + ['--cat', '--path=' + relative, cygpath(image)]
    )
    result = subprocess.run(command, check=True, capture_output=True)
    destination.write_bytes(result.stdout)


recipe_paths = list(args.recipe_dir.glob('*.json'))
if args.present_fence_bridge:
    recipe_paths.append(REPO / 'patches/display/present-fence-export.json')
for recipe_path in recipe_paths:
    extract_guard(json.loads(recipe_path.read_text(encoding='utf-8'))['path'])
for path in [
    '/system/lib64/libaccountmgr.z.so',
    '/system/lib64/chipset-sdk/libhukssdk.z.so',
    '/system/lib64/chipset-sdk-sp/libcrypto_openssl.z.so',
    '/sys_prod/etc/param/hw_defaults.para',
    '/system/etc/sandbox/appdata-sandbox.json',
    '/system/etc/sandbox/appdata-sandbox-isolated.json',
    '/system/etc/init/task_manager_service.cfg',
    '/system/profile/task_manager_service.json',
]:
    extract_guard(path)
for name in ['appdata-sandbox.json', 'appdata-sandbox-isolated.json']:
    extract_guard('/system/etc/sandbox/' + name, previous=True)
old = vr.parse((WORK / 'base.cpio').read_bytes())
new = dict(old)


# 复制文件元数据，避免改动原始归档
def setfile(name, data, mode=0o100644):
    if isinstance(data, str):
        data = data.encode()
    if name in new:
        fields = new[name][0].copy()
    else:
        fields = [
            max(v[0][0] for v in new.values()) + 1,
            mode,
            0,
            0,
            1,
            0,
            len(data),
            0,
            0,
            0,
            0,
            len(name.encode()) + 1,
            0,
        ]
    fields[1] = mode
    fields[6] = len(data)
    new[name] = (fields, data)


def text(name):
    return old[G + name][1].decode()


def sha(b):
    return hashlib.sha256(b).hexdigest()


# 核对新显示库的架构、导出及平台 C++ ABI
composer_report = None
if args.composer:
    blob = args.composer.read_bytes()
    if sha(blob) != args.composer_sha256:
        raise ValueError('Composer input hash mismatch')
    # 真实呈现反馈必须配套输出描述符清理补丁
    if (b'PRESENT_FENCE first_fd=' in blob) != args.present_fence_bridge:
        raise ValueError('Composer and present fence bridge must be paired')
    elf = ELFFile(io.BytesIO(blob))
    if elf['e_machine'] != 'EM_AARCH64' or elf['e_type'] != 'ET_DYN':
        raise ValueError('Composer must be an AArch64 shared library')
    symbols = list(elf.get_section_by_name('.dynsym').iter_symbols())
    exports = {s.name for s in symbols if s['st_shndx'] != 'SHN_UNDEF'}
    header = (REPO / 'compat/display/include/vdi-only/composer_exports.h').read_text(
        encoding='utf-8'
    )
    required = set(re.findall(r'extern "C" int32_t (\w+)\(', header))
    if not required <= exports or any('__n1' in s.name for s in symbols):
        raise ValueError('Composer VDI exports or platform C++ ABI mismatch')
    needed = {
        t.needed
        for t in elf.get_section_by_name('.dynamic').iter_tags()
        if t.entry.d_tag == 'DT_NEEDED'
    }
    if not needed <= {'libc++.so', 'libc.so'}:
        raise ValueError('Unexpected composer runtime dependency')
    member = G + 'libdisplay_composer_vdi_impl.z.so'
    composer_report = {
        'input_sha256': sha(old[member][1]),
        'output_sha256': sha(blob),
        'required_exports_checked': len(required),
        'needed': sorted(needed),
    }
    setfile(member, blob)


# 仅调整解锁标记常量，保留全部指令和其余启动判据
bootlib = P + 'bootcontrol-v135/libsheng_bootcontrol_guarded_v135.so'
guard = old[bootlib][1]
assert sha(guard) == '92db6e9f567ba53854d5dd84b2143ce6f65fca9b9b7555d5b5fc39a4b8dc5430'
old_marker = b'SCREENLOCK_VERIFIED after=0 callback=0'
new_marker = b'SCREENLOCK_VERIFIED after=0 '
assert guard.count(old_marker) == 1
marker_offset = guard.index(old_marker)
replacement = new_marker + bytes(len(old_marker) - len(new_marker))
section = ELFFile(io.BytesIO(guard)).get_section_by_name('.rodata')
assert (
    section is not None
    and section['sh_offset'] <= marker_offset
    and marker_offset + len(old_marker) <= section['sh_offset'] + section['sh_size']
)
fixed_guard = guard[:marker_offset] + replacement + guard[marker_offset + len(old_marker) :]
setfile(bootlib, fixed_guard)
checksums = old[P + 'bootcontrol-v135/SHA256SUMS'][1].decode().replace(sha(guard), sha(fixed_guard))
setfile(P + 'bootcontrol-v135/SHA256SUMS', checksums)
setfile(
    G + 'mark-boot-success-v135.sh',
    (REPO / 'runtime/compat/graphics/mark-boot-success-v135.sh').read_bytes(),
    0o100755,
)
bootcontrol_report = {
    'input_sha256': sha(guard),
    'output_sha256': sha(fixed_guard),
    'offset': marker_offset,
    'before': old_marker.hex(),
    'after': replacement.hex(),
    'instructions_unchanged': True,
    'other_native_gates_unchanged': True,
    'exact_unlock_variants_checked_by_launcher': True,
}
recipes = {}
for path in sorted(recipe_paths):
    recipe = json.loads(path.read_text(encoding='utf-8'))
    source = ROOT / 'metadata/guard-inputs' / recipe['path'].lstrip('/')
    blob = source.read_bytes()
    assert sha(blob) == recipe['input_sha256']
    patched = bytearray(blob)
    for change in recipe['changes']:
        at = change['offset']
        before = bytes.fromhex(change['before'])
        after = bytes.fromhex(change['after'])
        assert len(before) == len(after) and patched[at : at + len(before)] == before
        patched[at : at + len(after)] = after
    assert sha(patched) == recipe['output_sha256']
    destination = WORK / 'patched' / recipe['path'].lstrip('/')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(patched)
    recipes[recipe['path']] = recipe
# 在启动归档内暂存补丁，不修改原始供体镜像
fields = [
    max(v[0][0] for v in new.values()) + 1,
    0o40755,
    0,
    0,
    2,
    0,
    0,
    0,
    0,
    0,
    0,
    len((G + 'promax').encode()) + 1,
    0,
]
new[G + 'promax'] = (fields, b'')
for path, recipe in recipes.items():
    name = path.rsplit('/', 1)[1]
    setfile(
        G + 'promax/' + name,
        (WORK / 'patched' / path.lstrip('/')).read_bytes(),
        0o100755 if name == 'init' else 0o100644,
    )
# 同步替换兼容库及其输入哈希
for name in [
    'libaudio_policy_client.z.so',
    'libcode_sign_utils.z.so',
    'libsensor_client.z.so',
    'libsps_privacy_indicator_service_intf.z.so',
    'libwifi_sdk.z.so',
    'libnet_tether_manager_if.z.so',
]:
    matches = [(p, r) for p, r in recipes.items() if p.endswith('/' + name)]
    assert len(matches) == 1
    setfile(G + name, (WORK / 'patched' / matches[0][0].lstrip('/')).read_bytes())


# 生成带输入、输出哈希检查的挂载准备脚本
def stage(path, target=None, bind=False):
    recipe = recipes[path]
    name = path.rsplit('/', 1)[1]
    target = target or '/hmos-root/compat/lib64/' + name
    source = '/hmos-root' + path
    result = (
        f'echo "{recipe["input_sha256"]}  {source}" | $B sha256sum -c -\n'
        f'$B cp /graphics/promax/{name} {target}\n'
        f'echo "{recipe["output_sha256"]}  {target}" | $B sha256sum -c -\n'
        '$B chmod ' + ('0755' if name == 'init' else '0644') + f' {target}\n'
    )
    if bind:
        result += f'$B mount --bind {target} {source}\n'
    return result


head = '#!/busybox sh\nset -eu\nB=/busybox\nR=/hmos-root\n'
start = text('apply-compat-paths.sh').index('/busybox gzip -dc /graphics/libvulkan_freedreno.so.gz')
compat = (
    head
    + '$B mkdir -p $R/compat/bin $R/compat/lib64\n'
    + stage('/system/bin/init', '/hmos-root/compat/bin/init')
    + stage('/system/lib64/libvulkan.so')
    + text('apply-compat-paths.sh')[start:]
)
if args.present_fence_bridge:
    # 在原生显示服务启动前替换输出 fence 导出逻辑
    compat += stage('/vendor/lib64/libdisplay_composer_service_1.5.z.so', bind=True)
setfile(G + 'apply-compat-paths.sh', compat, 0o100755)
render = '/system/lib64/librender_service_base.z.so'
rh = recipes[render]['output_sha256']
setfile(
    G + 'apply-rosen-handle.sh',
    head + stage(render) + 'echo PROMAX_ROSEN_PATCH_SET_STAGED\n',
    0o100755,
)
for name in ['apply-render-usage.sh', 'apply-rs-commit-sync-v1.sh']:
    setfile(
        G + name,
        head
        + f'echo "{rh}  $R/compat/lib64/librender_service_base.z.so" | $B sha256sum -c -\necho PROMAX_ROSEN_PATCH_SET_VERIFIED\n',
        0o100755,
    )
setfile(
    G + 'apply-framework-dev.sh',
    head
    + stage('/system/lib64/libcode_sign_utils.z.so')
    + 'echo PROMAX_DEVELOPMENT_CODE_SIGN_COMPAT_STAGED\n',
    0o100755,
)
for script, path in [
    ('apply-cli-wait-v1.sh', '/system/lib64/platformsdk/libcli_tool_client.z.so'),
    ('apply-msdp-local-v1.sh', '/system/lib64/libdevicestatus_service.z.so'),
    ('apply-audio-wait-v1.sh', '/system/lib64/libaudio_policy_service.z.so'),
    ('apply-time-v1.sh', '/system/lib64/libtime_system_ability.z.so'),
    ('apply-memmgr-v2.sh', '/system/lib64/libmemmgrservice.z.so'),
]:
    body = head
    if script == 'apply-msdp-local-v1.sh':
        body += '$B sh /graphics/apply-storage-local-v1.sh\n'
    body += (
        stage(path, bind=True)
        + 'echo PROMAX_GUARDED_'
        + script.replace('-', '_').replace('.', '_')
        + '_STAGED\n'
    )
    setfile(G + script, body, 0o100755)
# 保留密钥目录准备流程，替换新版加密库
db = text('apply-db-key-v2.sh').split('S="$R/system/lib64/librelational_store_crypt.z.so"', 1)[0]
for name in [
    'librelational_store_crypt.z.so',
    'libkv_store_crypt.z.so',
    'libdistributeddatasvcfwk.z.so',
]:
    db += stage('/system/lib64/' + name, bind=True)
db += 'echo PROMAX_DB_KEY_BRIDGE_STAGED\n'
setfile(G + 'apply-db-key-v2.sh', db, 0o100755)
# 核对 Hks 接口及加密库导出符号
hmac = text('apply-account-hmac.sh')
account_checks = []
for path in [
    '/system/lib64/libaccountmgr.z.so',
    '/system/lib64/chipset-sdk/libhukssdk.z.so',
    '/system/lib64/chipset-sdk-sp/libcrypto_openssl.z.so',
]:
    data = (ROOT / 'metadata/guard-inputs' / path.lstrip('/')).read_bytes()
    digest = sha(data)
    line = next(l for l in hmac.splitlines() if path in l and 'sha256sum' in l)
    expected = re.search(r'\bin ([0-9a-f]{64})', line)[1]
    hmac = hmac.replace(expected, digest)
    account_checks.append({'path': path, 'input_sha256': digest})
huks = (ROOT / 'metadata/guard-inputs/system/lib64/chipset-sdk/libhukssdk.z.so').read_bytes()
symbols = ELFFile(io.BytesIO(huks)).get_section_by_name('.dynsym')
exports = {s.name for s in symbols.iter_symbols() if s['st_shndx'] != 'SHN_UNDEF'}
required = {'HksKeyExist', 'HksGenerateKey', 'HksInit', 'HksUpdate', 'HksFinish', 'HksAbort'}
assert required <= exports
setfile(G + 'apply-account-hmac.sh', hmac, 0o100755)
# 保留供体机型参数，按显示后端启用刷新率设置入口
cap = (ROOT / 'metadata/guard-inputs/sys_prod/etc/param/hw_defaults.para').read_bytes()
assert cap.count(b'const.nearlink.enable=true') == 1
newcap = cap.replace(b'const.nearlink.enable=true', b'const.nearlink.enable=false')
refresh_report = None
if args.composer:
    before = b'const.settings.refresh_rate_seenable=false'
    if newcap.count(before) != 1:
        raise ValueError('Unexpected refresh settings capability')
    newcap = newcap.replace(before, b'const.settings.refresh_rate_seenable=true', 1)
setfile(G + 'hw_defaults-v141.para', newcap)
hardware = text('apply-hardware-v116.sh')
hardware = hardware.replace(
    '47e94ce212bf301531e1e0f6480f9b4c566296a557e8fc03b44d958ed81fe8a2', sha(cap)
).replace('3fa79d36281510333d96de8ff23844e40229b1d227ada18ca0eff2fbf24a9dc2', sha(newcap))
if args.composer:
    # 覆盖挂载已校验的策略文件，保留原始供体镜像
    policy_path = '/sys_prod/etc/graphic/hgm_policy_config.xml'
    extract_guard(policy_path)
    policy = (ROOT / 'metadata/guard-inputs' / policy_path.lstrip('/')).read_bytes()
    if sha(policy) != INPUT_SHA256:
        raise ValueError('Refresh policy donor hash mismatch')
    updated_policy = patch_policy(policy)
    setfile(G + 'promax/hgm_policy_config.xml', updated_policy)
    hardware += (
        f'echo "{sha(policy)}  $R{policy_path}" | $B sha256sum -c -\n'
        '$B cp /graphics/promax/hgm_policy_config.xml "$R/compat/etc/hgm_policy_config.xml"\n'
        f'echo "{sha(updated_policy)}  $R/compat/etc/hgm_policy_config.xml" | $B sha256sum -c -\n'
        f'$B mount --bind "$R/compat/etc/hgm_policy_config.xml" "$R{policy_path}"\n'
    )
    refresh_report = {
        'path': policy_path,
        'input_sha256': sha(policy),
        'output_sha256': sha(updated_policy),
        'high_mode_hz': 144,
        'standard_and_auto_preserved': True,
        'runtime_validated': False,
    }
if args.refresh_helper:
    helper = args.refresh_helper.read_bytes()
    elf = ELFFile(io.BytesIO(helper))
    if sha(helper) != args.refresh_helper_sha256 or elf['e_machine'] != 'EM_AARCH64':
        raise ValueError('Refresh helper hash or architecture mismatch')
    setfile(G + 'promax/native_refresh_rate', helper, 0o100755)
    hardware += (
        '$B cp /graphics/promax/native_refresh_rate "$R/compat/bin/native_refresh_rate"\n'
        '$B chmod 0755 "$R/compat/bin/native_refresh_rate"\n'
        '$B touch "$R/data/local/tmp/sheng-refresh-request.txt" "$R/data/local/tmp/sheng-refresh-result.txt"\n'
        '$B chown 2000:2000 "$R/data/local/tmp/sheng-refresh-request.txt" "$R/data/local/tmp/sheng-refresh-result.txt"\n'
        '$B chmod 0600 "$R/data/local/tmp/sheng-refresh-request.txt" "$R/data/local/tmp/sheng-refresh-result.txt"\n'
    )
    refresh_report['helper_sha256'] = sha(helper)
setfile(G + 'apply-hardware-v116.sh', hardware, 0o100755)
preload = text('apply-preload.sh').replace('/preload/WKI-W10/all/cn', '/preload/GEM-W00/all/cn')
# 显式补入中国区资源层，恢复主题及动态图标
region = '/sys_prod/variant/region_comm/china'
file_index = json.loads((ROOT / 'metadata/sys_prod-files.json').read_text(encoding='utf-8'))
assert any(
    x['path'] == '/variant/region_comm/china/resource/themes/icon' and x['type'] == 'DIR'
    for x in file_index
)
if args.experimental_regional_resources:
    preload += (
        '\n$B printf "\\n# sheng: GEM-W00 regional resource policy\\n'
        '/sys_prod/variant/region_comm/china\\n" '
        '>> "$R/compat/etc/cust/baselayer.cfg"\n'
    )
setfile(G + 'apply-preload.sh', preload, 0o100755)
# 迁移沙箱兼容差异并保留新版字段
sandbox = text('apply-app-sandbox.sh')
sandbox_report = []
for name in ['appdata-sandbox.json', 'appdata-sandbox-isolated.json']:
    oldbytes = (ROOT / 'metadata/old-guard-inputs/system/etc/sandbox' / name).read_bytes()
    newbytes = (ROOT / 'metadata/guard-inputs/system/etc/sandbox' / name).read_bytes()
    patched_old = gzip.decompress(old[G + name + '.gz'][1])
    original = oldbytes.decode().splitlines(keepends=True)
    patched = patched_old.decode().splitlines(keepends=True)
    result = newbytes.decode()
    opcodes = difflib.SequenceMatcher(None, original, patched, autojunk=False).get_opcodes()
    edits = 0
    for tag, a, b, c, d in opcodes:
        if tag == 'equal':
            continue
        lo = max(0, a - 6)
        hi = min(len(original), b + 6)
        before = ''.join(original[lo:hi])
        after = ''.join(original[lo:a] + patched[c:d] + original[b:hi])
        assert result.count(before) == 1, (name, a, b, 'ambiguous sandbox context')
        result = result.replace(before, after, 1)
        edits += 1
    output = result.encode()
    assert (
        json.loads(output)['create-only-on-daemon'] == json.loads(newbytes)['create-only-on-daemon']
    )
    sandbox = sandbox.replace(sha(oldbytes), sha(newbytes)).replace(sha(patched_old), sha(output))
    setfile(G + name + '.gz', gzip.compress(output, mtime=0))
    sandbox_report.append(
        {
            'path': '/system/etc/sandbox/' + name,
            'input_sha256': sha(newbytes),
            'output_sha256': sha(output),
            'context_checked_edits': edits,
            'donor_additions_preserved': True,
        }
    )
setfile(G + 'apply-app-sandbox.sh', sandbox, 0o100755)
# 将音频策略覆盖挂载到供体现有目录
audio = text('apply-audio-v116.sh').replace(
    '[ ! -e "$R/chip_prod/etc/audio" ]\n$B ln -s /compat/etc/audio "$R/chip_prod/etc/audio"',
    '[ -d "$R/chip_prod/etc/audio" ]\n$B mount --bind "$R/compat/etc/audio" "$R/chip_prod/etc/audio"',
)
assert audio != text('apply-audio-v116.sh')
setfile(G + 'apply-audio-v116.sh', audio, 0o100755)
# 延后启动桌面依赖服务，保留供体身份及权限
task_cfg_path = ROOT / 'metadata/guard-inputs/system/etc/init/task_manager_service.cfg'
task_profile_path = ROOT / 'metadata/guard-inputs/system/profile/task_manager_service.json'
task_cfg = json.loads(task_cfg_path.read_text(encoding='utf-8'))
task_profile = json.loads(task_profile_path.read_text(encoding='utf-8'))
assert task_profile['process'] == 'task_manager_service'
assert len(task_profile['systemability']) == 1 and task_profile['systemability'][0]['name'] == 65984
assert task_profile['systemability'][0]['depend'] == [3299]
task_service = task_cfg['services'][0]
assert (
    task_service['name'] == 'task_manager_service' and task_service['uid'] == 'task_manager_service'
)
assert task_service['path'] == ['/system/bin/sa_main', '/system/profile/task_manager_service.json']
task_service['disabled'] = True
assert task_profile['systemability'][0]['start-on-demand']['param'] == [
    {'name': 'const.taskmanager_service.support', 'value': 'true'}
]
task_profile['systemability'][0]['start-on-demand']['param'] = [
    {'name': 'sheng.debug.start.promaxtask', 'value': 'true'}
]
task_profile_bytes = (json.dumps(task_profile, indent=2) + '\n').encode()
setfile(G + 'promax/task_manager_service.json', task_profile_bytes)
desktop = json.loads(text('init-desktop-services.cfg'))
assert all(s['name'] != 'task_manager_service' for s in desktop['services'])
desktop['services'].append(task_service)
prepare = next(j['cmds'] for j in task_cfg['jobs'] if j['name'] == 'post-fs-data')
desktop['jobs'].append(
    {
        'name': 'param:sheng-promax-task',
        'condition': 'sheng.debug.start.screen=true',
        'cmds': prepare + ['setparam sheng.debug.start.promaxtask true'],
    }
)
if args.refresh_helper:
    # 通过原生 init 分配身份，独立执行刷新率请求
    service = next(s.copy() for s in desktop['services'] if s['name'] == 'sheng_display_wake')
    service['name'] = 'sheng_refresh_rate'
    service['path'] = ['/compat/bin/native_refresh_rate']
    desktop['services'].append(service)
    desktop['jobs'].append(
        {
            'name': 'param:sheng-refresh-rate',
            'condition': 'sheng.debug.refresh.request=true',
            'cmds': ['start sheng_refresh_rate'],
        }
    )
setfile(G + 'init-desktop-services.cfg', json.dumps(desktop, indent=2) + '\n')
task_service_report = {
    'service': 'task_manager_service',
    'sa': 65984,
    'donor_cfg_sha256': sha(task_cfg_path.read_bytes()),
    'donor_profile_sha256': sha(task_profile_path.read_bytes()),
    'staged_profile_sha256': sha(task_profile_bytes),
    'startup_gate': 'sheng.debug.start.screen -> prepare directories -> sheng.debug.start.promaxtask',
    'donor_permissions_preserved': True,
    'hardware_sysfs_jobs_imported': False,
    'runtime_validated': False,
}
# 添加供体软件区域参数，保持硬件标识不变
cust_parameters = {
    'const.cust.devmodel': 'GEM-W00',
    'const.cust.vendor': 'all',
    'const.cust.region': 'cn',
    'const.cust.home_region': 'cn',
}
cust_path = '/system/etc/param/sheng_promax_cust.para'
assert not any(
    x['path'] == cust_path
    for x in json.loads((ROOT / 'metadata/system-files.json').read_text(encoding='utf-8'))
)
cust_output = (
    b'# sheng: verified GEM-W00 all/cn donor software layers\n'
    + ''.join(k + '=' + v + '\n' for k, v in cust_parameters.items()).encode()
)
if args.experimental_regional_resources:
    setfile(G + 'promax/sheng_promax_cust.para', cust_output)
cust_report = {
    'enabled': args.experimental_regional_resources,
    'path': cust_path,
    'new_file': True,
    'output_sha256': sha(cust_output),
    'parameters': cust_parameters,
    'explicit_regional_policy_layer': region if args.experimental_regional_resources else None,
    'hardware_identity_parameters_changed': False,
    'dynamic_icon_runtime_validated': False,
    'existing_theme_cache_may_require_reapply': True,
}
# 核对保存在 userdata 内的附加只读镜像
seed_names = ['preload', 'chip_prod', 'anco_hmos', 'cust', 'version']
seed_lines = []
for name in seed_names:
    folder = 'preload' if name == 'preload' else 'cust' if name == 'version' else 'base'
    img = ROOT / 'extracted' / folder / (name + '.img')
    report = json.loads(
        (ROOT / 'extracted' / folder / 'extraction-report.json').read_text(encoding='utf-8')
    )
    record = next(c for c in report['components'] if c['name'] == name)
    assert record['hash_verified'] and record['extracted']
    seed_lines.append(record['sha256'] + '  ' + name + '.img')
setfile(G + 'promax/seed-images.sha256', '\n'.join(seed_lines) + '\n')
mount = '''#!/busybox sh
set -eu
B=/busybox
R=/hmos-root
S=$R/data/hmos-promax
$B test -d "$S"
$B chown -R 0:0 "$S"
$B chmod 0700 "$S"
$B chmod 0600 "$S"/*.img
cd "$S"
$B sha256sum -c /graphics/promax/seed-images.sha256
# 按内核实际设备号创建 loop 节点
for sysdir in /sys/class/block/loop[0-9]*; do
 name=${sysdir##*/}
 case "${name#loop}" in ''|*[!0-9]*) continue;; esac
 [ -r "$sysdir/dev" ] || continue
 nums=$($B cat "$sysdir/dev")
 $B rm -f "/dev/$name"
 $B mknod "/dev/$name" b "${nums%:*}" "${nums#*:}"
 $B chmod 0600 "/dev/$name"
done
$B test -b /dev/loop0
for name in preload chip_prod anco_hmos cust version; do
 lower=/hmos/promax-$name
 $B mkdir -p "$lower" "$R/$name"
 loop=$($B losetup -f)
 $B losetup -r "$loop" "$S/$name.img"
 $B mount -t erofs -o ro,nosuid,nodev "$loop" "$lower"
 if [ "$name" = chip_prod ] || [ "$name" = preload ]; then
  upper=/hmos-ram/promax-$name-upper
  work=/hmos-ram/promax-$name-work
  $B mkdir -p "$upper" "$work"
  $B mount -t overlay -o lowerdir="$lower",upperdir="$upper",workdir="$work" overlay "$R/$name"
 else
  $B mount --bind "$lower" "$R/$name"
  $B mount -o remount,bind,ro,nosuid,nodev "$R/$name"
 fi
 echo "PROMAX_SEED_MOUNTED name=$name loop=$loop"
done
# 仅挂载安卓容器载荷，不启动后端
echo PROMAX_CONTAINER_FILES_PRESENT_RUNTIME_NOT_VALIDATED
'''
setfile(G + 'promax/mount-seed-images.sh', mount, 0o100755)
userdata = text('init-userdata-ext4.sh') + '\n$B sh /graphics/promax/mount-seed-images.sh\n'
setfile(G + 'init-userdata-ext4.sh', userdata, 0o100755)
userdata += (
    f'echo "{sha(task_profile_path.read_bytes())}  $R/system/profile/task_manager_service.json" '
    '| $B sha256sum -c -\n'
    '$B cp /graphics/promax/task_manager_service.json '
    '"$R/system/profile/task_manager_service.json"\n'
    f'echo "{sha(task_profile_bytes)}  $R/system/profile/task_manager_service.json" '
    '| $B sha256sum -c -\n'
)
if args.experimental_regional_resources:
    userdata += (
        f'$B test ! -e "$R{cust_path}"\n'
        f'$B cp /graphics/promax/sheng_promax_cust.para "$R{cust_path}"\n'
        f'echo "{sha(cust_output)}  $R{cust_path}" | $B sha256sum -c -\n'
    )
setfile(G + 'init-userdata-ext4.sh', userdata, 0o100755)
# 更新全部兼容组件的大小和哈希
manifest = json.loads(old[P + 'MANIFEST.json'][1])
members = set(manifest)
for name in new:
    if name.startswith(G + 'promax/') and (new[name][0][1] & 0o170000) == 0o100000:
        members.add(name[len(P) :])
for relative in sorted(members):
    fields, blob = new[P + relative]
    manifest[relative] = {'bytes': len(blob), 'mode': oct(fields[1]), 'sha256': sha(blob)}
setfile(P + 'MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
changed = {n for n in new if n not in old or new[n] != old[n]}
added = set(new) - set(old)
report = {
    'donor': 'GEM-LGRP3-CHN 207.0.0.111(SP12)',
    'base_vendor_boot_sha256': sha(base.read_bytes()),
    'changed_entries': sorted(changed),
    'added_entries': sorted(added),
    'patch_recipes': len(recipes),
    'account_input_checks': account_checks,
    'seed_checksums': seed_lines,
    'boot_unchanged': True,
    'init_boot_unchanged': True,
    'dtb_unchanged': True,
    'kernel_unchanged': True,
    'device_boot_tested': False,
    'features_not_validated': ['144Hz', 'Zhuoyitong Android backend', 'all application GPU paths'],
}
(WORK / 'payload-integration-report.json').write_text(
    json.dumps(report, indent=2) + '\n', encoding='utf-8'
)
report['sandbox_port'] = sandbox_report
report['promax_task_service'] = task_service_report
report['bootcontrol_unlock_marker'] = bootcontrol_report
report['donor_software_layers'] = cust_report
report['display_composer'] = composer_report
report['present_fence_bridge'] = args.present_fence_bridge
report['refresh_policy'] = refresh_report
# 导出生成脚本并检查 Shell 语法
scripts = WORK / 'integrated-scripts'
scripts.mkdir(exist_ok=True)
for n in changed:
    if n.endswith('.sh'):
        dest = scripts / n.rsplit('/', 1)[1]
        dest.write_bytes(new[n][1])
        subprocess.run([r'C:\Program Files\Git\bin\bash.exe', '-n', str(dest)], check=True)


# 仅替换已核对的归档成员
def mutate(entries):
    for name in sorted(changed):
        entries[name] = new[name]


image = vr.edit(
    base, report['base_vendor_boot_sha256'], WORK / 'vendor-boot-repack', mutate, changed, added
)
destination = WORK / 'vendor_boot_promax_111sp12.img'
destination.write_bytes(image)
report['vendor_boot_sha256'] = sha(image)
report['vendor_boot_bytes'] = len(image)
report['cpio_roundtrip_verified'] = True
(WORK / 'payload-integration-report.json').write_text(
    json.dumps(report, indent=2) + '\n', encoding='utf-8'
)
print(json.dumps(report, indent=2), flush=True)
