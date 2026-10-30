from pathlib import Path
from datetime import datetime
import json

root = Path(__file__).resolve().parent.parent
stamp = datetime.now().astimezone().isoformat(timespec='seconds')
text = f'''# 当前移植状态

更新时间：{stamp}。本节取代所有旧版状态及旧版 vendor 授权。

**当前设备 YOUR_DEVICE_SERIAL 正在运行 v46 Probe / ShengExports 5.15.178；不在 Recovery。屏幕方块是诊断素材，未进入桌面。用户本轮再次确认仍是方块界面。**

- 三启动镜像：ShengExports boot、原303 vendor_boot、v46 init_boot（SHA256 f3686a1553649e77708248147a7d06a17e7d44c2613fe3a57b1641de9e26b15a）。
- vendor/vendor_dlkm 已通过 EROFS 只读 bind 验证，未覆盖 vendor 文件或 init 目录；原 composer SHA 与原镜像一致。原 HDI 实际映射私有 /compat/lib64 VDI，Vulkan、固件与 Rosen 修正均迁入独立兼容层。
- v46 首轮 GPU 失败为 firmware_class 路径带 /hmos-root 前缀，chroot 内不可见；运行时改为 /compat/firmware 后，原生 Rosen GPU 合约返回0，RenderService 重启，GPU→RS→HDI 实际扫描读回成功。不是桌面或系统截图 API 成功。
- 最近进程：allocator322、composer323、watcher399、scheduler401、AccessToken402、RenderService836、installs896。foundation455 在 ctl.stop 返回成功后仍存在，不能把返回成功当停服。
- 原 installs / SA511 已真实 Publish result0。此前 BMS 等待511的阻点有了新的前提，接下来限时重试原角色 foundation 应用核心。BMS/AMS/AppMgr/SceneBoard 未验收，触摸和 WiFi 未验收。
- 3048×2032 实际扫描数据已压缩在 /hmos-root/data/local/tmp/v46-actual.ppm.gz：52079字节，SHA256 6b667f80cf2c48ec4d0955c82916bc3a4fd4140ccabd80007655ecbf6ea98bb3。待传回；诊断图不冒充桌面截图。默认 snapshot_display API 之前仍黑。
- v47 已构建并完整解包验证，尚未刷入；修正固件路径。init_boot SHA256 9ed9d64c70f437232bf4cec46d119949b52127e52ee4af2a6c6082bf2a42c31a。当前源码v47，回退应使用已保存镜像，不用旧builder重编旧版本。
- 独立层资产持久存于版本化 init_boot；原init第二阶段和私有库在启动时自动接入。不过 GPU 模块和核心服务门控仍手动触发，完整无人值守开机未完成。
- AnyHarmonyOS 参考 /root/hmos-reference/AnyHarmonyOS，commit cb1ce16e71392404ecb56f812380ac18c7085520。用户要求 BMS/AccessToken 复用该仓库代码；优先原角色、权限、目录及启动顺序，按精确输入SHA选择补丁。仓库没有可直接替代原BMS的完整服务，不能宣称已复用修好；不引入暂停的音频/壁纸实验，不commit/push。
- 最新约束：所有硬件修正在独立兼容层，不动vendor，也不覆盖vendor路径；保留原镜像/真实userdata/三启动备份。卡fastboot或进不去Recovery先恢复实际备份boot、vendor_boot、init_boot三者。
- 21:37 定时任务已删除，用户要求现在继续，无替代任务。当前账户工具未暴露数值额度，不得把历史93%或重置时间当当前实查；保留2%–3%善后、1%前停止规则。
- 摄像头未开启。无并发刷写/串口控制。停止前必须回Recovery、验证ADB并导出日志更新文档。

## 本轮已验证

1. v46 冷启动兼容层接入、vendor只读且原文件哈希保持；原 init 从 /compat/bin/init 执行。
2. 修正固件查找路径后 ROSEN_GPU_CONTRACT=0；RS重新启动；plane90/fb66，3048×2032、pitch12288，CAPTURE_RC0。
3. 原角色 installs 的 SA511 发布成功；BMS尚未因此自动通过。
4. v47 离线容器/资产与原Android init保存检查通过，未实刷。

## 下一步与真实限制

- 先取回本轮扫描数据和日志，再限时验证511之后的BMS/AMS/AppMgr实际错误；保持原foundation UID/token，不root直启。
- 参考 AnyHarmonyOS 的 persist.bms.test-upgrade=false、目录权限/restorecon、原服务链；任何二进制补丁都核对当前输入SHA及实际错误，不盲套其他原包偏移。
- 确认framework后推进appspawn和SceneBoard；未获得真实桌面之前，不把方块画面记作完成。
- v47需下一轮冷启动验收；完整开机自动化、系统截图API、触摸与WiFi仍未完成。

## 证据

- output/logs/command-shell-20261027-213720-94ea2c85cf6d.log（vendor只读/原composer哈希）
- output/logs/command-shell-20261027-214132-98bff1fb6177.log（兼容库真实映射与初次RS失败）
- output/logs/command-shell-20261027-214517-7116ccc22c13.log（固件查找-2）
- output/logs/command-shell-20261027-214559-2b15d521d2c8.log（固件路径修正及Rosen通过）
- output/logs/command-shell-20261027-214736-5e781dae377f.log（SCANOUT_CAPTURE及SA511发布）
- output/logs/command-shell-20261027-215143-52cb7898564d.log（截图gzip SHA及foundation仍在）
- analysis/v46-compat-layer.json、analysis/v47-image-verification.json、output/v47-manifest.json
'''
(root/'当前状态.md').write_text(text, encoding='utf-8')
for rel in ['analysis/续接检查点.md', 'analysis/轮次总结.md', 'analysis/20261027续接进展.md']:
    p=root/rel
    old=p.read_text(encoding='utf-8') if p.exists() else ''
    p.write_text(text+'\n\n---\n\n以下是历史记录；冲突时以上述最新状态和项目约束为准。\n\n'+old, encoding='utf-8')
with (root/'analysis/compat-vendor-readonly-plan.md').open('a', encoding='utf-8') as f:
    f.write('\n\n## '+stamp+' 迁移实际验收\n\n'+text)
(root/'analysis/round-20261027-2155.json').write_text(json.dumps({'time':stamp,'version':'v46','state':'Probe running, no desktop','vendor':'EROFS read-only binds; no vendor overlays','sa511':'published result0','v47':'built, verified, not flashed','quota':'numeric unavailable','checkpoint':'当前状态.md'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(stamp, 'saved current status and four records')
