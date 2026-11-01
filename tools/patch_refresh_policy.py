"""Adapt the GEM-W00 high-refresh setting to the sheng display backend."""

import re
import xml.etree.ElementTree as ET

INPUT_SHA256 = 'a78d77029b6fc9a5e509ea60a07824e1ed10aa1bc1380e357ec1fed6f5dc003d'


# 仅调整高刷分支，保留自动、标准及应用例外配置
def patch_policy(data):
    root = ET.fromstring(data)
    strategy = root.find('./Params[@name="refreshRate_strategy_config"]/Strategy[@name="14"]')
    if strategy is None or strategy.get('min') != '144' or strategy.get('max') != '144':
        raise ValueError('Expected fixed 144Hz strategy is absent')
    pattern = rb'(<Params name="screen_config" type="LTPO-DEFAULT">)(.*?)(</Params>)'
    screens = list(re.finditer(pattern, data, re.S))
    if len(screens) != 1:
        raise ValueError('Ambiguous primary screen policy')
    screen = screens[0]
    pattern = rb'<Setting id="2" strategy="8">.*?</Setting>'
    settings = list(re.finditer(pattern, screen[2], re.S))
    if len(settings) != 1:
        raise ValueError('Expected high-refresh setting is absent')
    setting = settings[0]
    original = setting[0]
    updated = original.replace(
        b'<Setting id="2" strategy="8">', b'<Setting id="2" strategy="14">', 1
    )
    # 高刷分支使用固定扫描时序，关闭未实现的 LTPO 控制
    for before, after in (
        (b'<Ltpo name="switch" value="1"/>', b'<Ltpo name="switch" value="0"/>'),
        (b'<Ltpo name="alignRate" value="120"/>', b'<Ltpo name="alignRate" value="144"/>'),
    ):
        if updated.count(before) != 1:
            raise ValueError('Unexpected LTPO setting')
        updated = updated.replace(before, after, 1)
    updated = updated.replace(b'preferred_fps="120"', b'preferred_fps="144"')
    updated = updated.replace(b'strategy="12"', b'strategy="14"')
    start = screen.start(2) + setting.start()
    end = screen.start(2) + setting.end()
    result = data[:start] + updated + data[end:]
    ET.fromstring(result)
    return result
