import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from private_persist_parameters import prepare_private_persist


class PrivatePersistParametersTests(unittest.TestCase):
    def setUp(self):
        self.config = (ROOT / 'runtime/compat/hmos-init-debug.cfg').read_bytes()
        self.template = '\n'.join([
            'BOOTSTRAP_SHA=@BOOTSTRAP_SHA@',
            'BASELINE_SHA=@BASELINE_SHA@',
            'CANDIDATE_SHA=@CANDIDATE_SHA@',
        ])

    def test_preserves_configuration_and_override_order(self):
        # 确认仅新增一次加载，后续基线参数仍保留原顺序
        output, helper, _ = prepare_private_persist(self.config, self.template, 'a' * 64)
        original = json.loads(self.config)
        candidate = json.loads(output)
        commands = next(job['cmds'] for job in candidate['jobs'] if job['name'] == 'pre-init')
        position = commands.index('load_private_persist_params ')
        self.assertEqual(commands[position - 1].strip(), 'load_persist_params')
        self.assertGreater(commands.index('setparam persist.bms.test-upgrade false'), position)
        commands.pop(position)
        self.assertEqual(candidate, original)
        self.assertIn(hashlib.sha256(output).hexdigest().encode(), helper)
        self.assertIn(hashlib.sha256(self.config).hexdigest().encode(), helper)

    def test_rejects_duplicate_load_and_template_identity_mismatch(self):
        output, _, _ = prepare_private_persist(self.config, self.template, 'a' * 64)
        with self.assertRaises(ValueError):
            prepare_private_persist(output, self.template, 'a' * 64)
        with self.assertRaises(ValueError):
            prepare_private_persist(self.config, self.template + '@BASELINE_SHA@', 'a' * 64)
        with self.assertRaises(ValueError):
            prepare_private_persist(self.config, self.template, 'not-a-digest')

    def test_rejects_configuration_that_would_exceed_bootstrap_buffer(self):
        # 阻止配置在原启动程序的固定读取缓冲区中截断
        config = json.loads(self.config)
        config['padding'] = 'x' * 32768
        with self.assertRaises(ValueError):
            prepare_private_persist(json.dumps(config).encode(), self.template, 'a' * 64)


if __name__ == '__main__':
    unittest.main()
