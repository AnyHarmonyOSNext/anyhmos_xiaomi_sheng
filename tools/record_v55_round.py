from pathlib import Path
from datetime import datetime
import json,hashlib,tarfile
r=Path(__file__).resolve().parent.parent
arc=r/'output/logs/v55-persistent-20261028-011543.tar'
with tarfile.open(arc) as f:
    assert len(f.getmembers())==20
    for m in f.getmembers():assert len(f.extractfile(m).read())==m.size
shot=r/'output/screenshots/v55-system-display0-20261028-0108.jpeg'
assert hashlib.sha256(shot.read_bytes()).hexdigest()=='a705b6ea044d63ee09d2b76395bf96bf66e508095ba3bcd1a5ed3b28964a169f'
t=datetime.now().astimezone().isoformat(timespec='seconds')
body=f'''## {t} v55 持久化、账户ready、SceneBoard和黑色系统截图；待测v56

设备已回TWRP/ADB/root；v55实刷，init_boot SHA47b1b55af825eef158a1798b479bed7e0173c45adee57707fb396b09e47ab49b，ShengExports5.15.178 boot+303 vendor_boot。第一轮漏加载IPC，未启动samgr；已重启按ipc成功→hmos顺序验证。不能将第一次失败当作新内核/持久化失败。v56加入handoff前模块存在门控。

真实userdata已接入持久化后端：TWRP中新建独立/data/hmos-compat，保留原recovery；data-v1.ext4为8GiB稀疏普通文件，标签HMOS_COMPAT，UUID76fb5f0c-a521-4461-948d-60f2204655dc，0600。只格式化这个新文件，没有格式化物理userdata。Probe先只读验证标记和文件长度，再把F2FS挂到新根之外/sheng-persistent；loop7把该文件挂为鸿蒙/data，ext4可写约7.8GiB。鸿蒙/dev仍不暴露物理userdata。重启后截图和20份日志均保留，持久化实证通过。源脚本compat/sheng-framework/persistent-v1/init-persistent-ext4.sh。

v55固化storage-ram-launcher和no-TEE桥，但pre-init未创建chipset/misc顶层，启动时已运行时补齐4类×5级父目录。原storage412/storage_manager460/账户476启动，3503/5003/200发布；配额请求本轮未重现此前几十秒延迟。BMS首扫安装190多个包因缺EL5服务8250反复等待，持续约20多分钟；未断言Binder驱动损坏。现场Binder账户476:488等待foundation596:762，后者参与BMS处理。

发现settingsdata反复孵化失败218103816：用户0数据目录不存在导致sandbox bind mount ENOENT。找到原sdc，调用/system/bin/sdc filecrypt init_main_user实际ret0，经原StorageDaemon InitGlobalUserKeys/PrepareAllUserEl1Dirs/PrepareAppdataDir创建全局el1目录。el2/0仍缺，不能称settingsdata已成功运行。原用户100账户记录最终isCreateCompleted=true，bootevent.account.ready=true。记录时isActived/isForeground/isLoggedIn仍false，不能将ready等同所有账户状态完成。

首次真实SceneBoard进程：com.ohos.sceneboard PID4092、后续4362，UID20020020；原JS已进入SceneBoardMainAbility、LaunchHomeCold、initThemeService。不是诊断方块。原snapshot_display在shell角色下生成display0.jpeg，97655字节、2032x3048；已取回并SHA校验、实际查看，内容全黑，仍没有真实桌面验收。原RS552存在但不能以进程存在宣称持续渲染。生成截图后USB消失再枚举，boot_id变为712b625d-dc74-4129-9382-ca355e751c4a且uptime约52秒，设备确实重新启动；根因未定，不自动归因截图/内核。原持久化文件在HOLD中以只读ext4重新挂载后取回截图。没有开摄像头。

证据：output/logs/command-shell-20261028-010159-a15f8db3252b.log(sdc ret0)、010555-b8ddce948d7c.log(账户ready及完成记录)、010638-0959a8951231.log(SceneBoard真实PID)、010800-90548fdde6db.log(截图生成)、010935-6a7e2a2430b5.log(新boot)、011001-a4e903f8eec1.log(持久化文件恢复)。系统截图output/screenshots/v55-system-display0-20261028-0108.jpeg SHA a705b6ea044d63ee09d2b76395bf96bf66e508095ba3bcd1a5ed3b28964a169f。20份原始日志output/logs/v55-persistent-20261028-011543.tar，3055104字节，SHA74f8851194913ec9ba8c2c011ac5ec6d27e03c3a6ef454e03cc980d0b016ae06；本地逐成员读取验证通过。

v56离线构建/解包验证通过，尚未刷：SHA331ef2499bcbb66c3c41da2d00c45969faa1477655861a4e568a82235079f6be。补顶层父目录，加入原sdc初始化门控、原foundation4606/3704、原theme_manager_service/wallpaper_service显式门控。给installs独立LD_PRELOAD桥，只对原EL5 GenerateAppKey/GenerateGroupIDKey立即返回-ENOTSUP，不生成密钥、不设置加密、不返回成功；目的是停止对不存在8250的长重试，尚未真机验证。真实桌面、物理屏幕、系统截图有内容仍未完成。下一轮先存储→sdc→KV/账户→图形→主题→完整窗口和SceneBoard，并抓SceneBoard/RS日志，避免再重复全量首扫。

全部兼容修复独立/compat，vendor/vendor_dlkm保持只读；无commit/push，无定时任务，无委派。额度数值查询工具不可用，不能声称查询剩余百分比。用户明确要求完成桌面目标前持续推进；此记录为轮次检查点，不是任务完成。
'''
for name in ['analysis/续接检查点.md','analysis/轮次总结.md','analysis/20261027续接进展.md']:
    p=r/name;p.write_text(body+'\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
(r/'当前状态.md').write_text('# 当前移植状态\n\n'+body,encoding='utf-8')
(r/'analysis/v55-framework.json').write_text(json.dumps({'version':'v55','status':'ACCOUNT_READY_SCENEBOARD_RUNNING_BLACK_SYSTEM_SCREENSHOT_RECOVERY','persistent_data':True,'account_ready':True,'account100_creation_complete':True,'account100_activated':False,'sceneboard_spawned':True,'desktop_verified':False,'screenshot_content':'black','recovery_adb':True,'next_candidate':'v56'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(t)
