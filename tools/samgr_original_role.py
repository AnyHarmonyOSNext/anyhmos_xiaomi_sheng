import copy
import hashlib
import json


SAMGR_CONFIG = '/system/etc/init/samgr_standard.cfg'
SAMGR_INPUTS = {
    SAMGR_CONFIG: '51d370c8329c337a9aeda43456088c5b4641f3bbd8737a371f27e326bdee7856',
}
ROLE_FIELDS = ('permission', 'permission_acls')
IDENTITY_FIELDS = ('path', 'uid', 'gid', 'secon', 'apl')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def samgr_service(config):
    if not isinstance(config, dict) or not isinstance(config.get('services'), list):
        raise ValueError('Invalid native init service list')
    services = config['services']
    if any(not isinstance(service, dict) for service in services):
        raise ValueError('Invalid native init service object')
    matches = [service for service in services if service.get('name') == 'samgr']
    if len(matches) != 1:
        raise ValueError('Expected one native SAMGR service')
    return matches[0]


# 校验原始声明，拒绝混用供体或未知权限列表
def validate_samgr_inputs(inputs):
    if set(inputs) != set(SAMGR_INPUTS):
        raise ValueError('Unexpected SAMGR input set')
    for path, expected in SAMGR_INPUTS.items():
        if digest(inputs[path]) != expected:
            raise ValueError('Original SAMGR config hash differs')
    service = samgr_service(json.loads(inputs[SAMGR_CONFIG]))
    permissions = service.get('permission')
    acls = service.get('permission_acls')
    if (
        not isinstance(permissions, list)
        or not isinstance(acls, list)
        or not all(isinstance(value, str) and value for value in permissions + acls)
        or len(permissions) != 22
        or len(set(permissions)) != 22
        or len(acls) != 2
        or len(set(acls)) != 2
        or not set(acls).issubset(permissions)
    ):
        raise ValueError('Original SAMGR role declaration differs')
    return service


# 仅恢复权限和 ACL，保留现有身份与启动策略
def restore_samgr_role(config, inputs):
    if not isinstance(config, bytes):
        raise ValueError('Native init config must be bytes')
    original = validate_samgr_inputs(inputs)
    candidate = json.loads(config)
    service = samgr_service(candidate)
    if any(service.get(key) != original.get(key) for key in IDENTITY_FIELDS):
        raise ValueError('Current SAMGR identity differs from the original role')
    existing = [key for key in ROLE_FIELDS if key in service]
    if existing and (
        len(existing) != len(ROLE_FIELDS)
        or any(service[key] != original[key] for key in ROLE_FIELDS)
    ):
        raise ValueError('Current SAMGR role is not the reviewed omitted state')
    if existing:
        output = config
    else:
        for key in ROLE_FIELDS:
            service[key] = copy.deepcopy(original[key])
        output = (json.dumps(candidate, indent=2) + '\n').encode()
    if len(output) >= 32768:
        raise ValueError('Native init config exceeds the bootstrap buffer')
    report = {
        'enabled': True,
        'service': 'samgr',
        'donor_inputs': SAMGR_INPUTS.copy(),
        'permission_count': len(original['permission']),
        'permission_acl_count': len(original['permission_acls']),
        'restored_fields': list(ROLE_FIELDS),
        'already_restored': bool(existing),
        'input_sha256': digest(config),
        'output_sha256': digest(output),
        'other_service_fields_preserved': True,
        'native_permission_guard_changed': False,
        'manual_token_database_changes': False,
        'runtime_validated': False,
    }
    return output, report
