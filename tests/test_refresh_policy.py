from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from patch_refresh_policy import patch_policy

POLICY = b'''<HgmConfig>
<Params name="refreshRate_strategy_config"><Strategy name="14" min="144" max="144"/></Params>
<Params name="screen_config" type="LTPO-DEFAULT">
<Setting id="-1" strategy="8"><Other preferred_fps="120"/></Setting>
<Setting id="1" strategy="4"/>
<Setting id="2" strategy="8">
<Ltpo name="switch" value="1"/><Ltpo name="alignRate" value="120"/>
<Other preferred_fps="120"/><Scene strategy="12"/><App strategy="4"/>
</Setting></Params></HgmConfig>'''


class RefreshPolicyTests(unittest.TestCase):
    # 核对修改范围，防止标准模式和应用例外随高刷配置改变
    def test_only_high_refresh_branch_changes(self):
        result = patch_policy(POLICY)
        self.assertIn(b'<Setting id="2" strategy="14">', result)
        self.assertIn(
            b'<Setting id="-1" strategy="8"><Other preferred_fps="120"/></Setting>', result
        )
        self.assertIn(b'<Setting id="1" strategy="4"/>', result)
        self.assertIn(b'<App strategy="4"/>', result)
        self.assertIn(b'<Ltpo name="switch" value="0"/>', result)
        self.assertIn(b'<Other preferred_fps="144"/>', result)
        self.assertIn(b'<Scene strategy="14"/>', result)

    def test_unknown_layout_is_rejected(self):
        for before, after in (
            (b'min="144"', b'min="120"'),
            (b'id="2" strategy="8"', b'id="2" strategy="13"'),
            (b'name="switch" value="1"', b'name="switch" value="0"'),
        ):
            with self.subTest(before=before), self.assertRaises(ValueError):
                patch_policy(POLICY.replace(before, after))


if __name__ == '__main__':
    unittest.main()
