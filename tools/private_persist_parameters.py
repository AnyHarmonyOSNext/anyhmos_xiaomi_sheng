import copy
import hashlib
import json
import re


def prepare_private_persist(config, template, bootstrap_sha256):
    # 保留原配置，仅在公共参数加载后补充原生完整加载
    if not re.fullmatch(r'[0-9a-f]{64}', bootstrap_sha256):
        raise ValueError('Invalid bootstrap identity')
    baseline = json.loads(config)
    candidate = copy.deepcopy(baseline)
    jobs = [job for job in candidate['jobs'] if job['name'] == 'pre-init']
    if len(jobs) != 1:
        raise ValueError('Expected one pre-init job')
    if any(
        command.strip() == 'load_private_persist_params'
        for job in candidate['jobs']
        for command in job.get('cmds', [])
    ):
        raise ValueError('Private persistent parameters are already loaded')
    commands = jobs[0]['cmds']
    positions = [
        index for index, command in enumerate(commands)
        if command.strip() == 'load_persist_params'
    ]
    if len(positions) != 1:
        raise ValueError('Expected one public persistent parameter load')
    commands.insert(positions[0] + 1, 'load_private_persist_params ')
    candidate_bytes = (json.dumps(candidate, indent=2) + '\n').encode()
    if len(candidate_bytes) >= 32768:
        raise ValueError('Init config exceeds the bootstrap buffer')

    # 将本次构建身份写入模板，失败时保留原启动配置
    replacements = {
        '@BOOTSTRAP_SHA@': bootstrap_sha256,
        '@BASELINE_SHA@': hashlib.sha256(config).hexdigest(),
        '@CANDIDATE_SHA@': hashlib.sha256(candidate_bytes).hexdigest(),
    }
    helper = template
    for marker, value in replacements.items():
        if helper.count(marker) != 1:
            raise ValueError('Unexpected persistent parameter template marker')
        helper = helper.replace(marker, value)
    return candidate_bytes, helper.encode(), replacements
