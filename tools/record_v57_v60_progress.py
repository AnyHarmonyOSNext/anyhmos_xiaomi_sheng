from pathlib import Path
from datetime import datetime
import hashlib,tarfile
r=Path(__file__).resolve().parent.parent
lines=[]
for n in ['v57-persistent-20261028-013524.tar','v58-persistent-20261028-014224.tar']:
 p=r/'output/logs'/n
 with tarfile.open(p) as t:
  for m in t.getmembers():assert m.isfile() and len(t.extractfile(m).read())==m.size
 lines.append(f'- output/logs/{n}，{p.stat().st_size}字节，SHA256 {hashlib.sha256(p.read_bytes()).hexdigest()}')
body=f'''## {datetime.now().astimezone().isoformat(timespec='seconds')} v57/v58 实测；v60 正在验证 SceneBoard 非阻塞查询

v57已实刷，原账户ready，SceneBoard PID860进入initSceneBoard ok、真实UIContent RunPage:pages/EntryView；仍6秒freeze/换PID，无桌面验收。冻结文件freeze_19700102112404_860.txt的主线程明确等待WifiSaLoadManager::WaitLoadStateChange / LoadWifiSa，经NetSpeedController.handleCheckNetwork同步调用。v57降低ptrace开销有效但未解决该真实等待。截图本次文件仍97655字节，未取回查看，不能称有内容；旧v55截图已确认黑色。v57随后重启，boot_id变252e6f5a-8ce8-4c95-b725-4b751e595c8f，原因未定。

v58实刷SHAe4f996f00900c735766d98c40872bd71dc9e4b5bb6576f3eba22367d565ff22e：独立compat配置加入原wifi_manager_service/原权限/数据目录，没有改vendor或WiFi内核驱动。初始按需调用被SAFWK权限拒绝（callingPid0/token671659553），后在RAM system profile仅将1120设run-on-create，原SA1120确实Publish result0；但chip_interface_service不存在，原服务随后反复退出，桌面仍同步等待WiFi并freeze。未声称WiFi已修复。v58再次重启至HOLD，boot_id9801bcc0-f015-4404-a3f5-85c3a4a07e55。已正常回TWRP并导出10MiB日志。

v59已构建/完整解包验证，未刷：仅appspawn加载独立libsheng_wifi_ui_unavailable.so，导出原LoadWifiSa ABI。只对cmdline恰为com.ohos.sceneboard且SA1120..1125立即返回原错误值1；其他进程转交RTLD_NEXT。没有伪造联网/启用成功。继承v57配置，放弃v58原WiFi服务实验。v59 Probe SHA8135f2dc0dfe579693df4f994c52ded3dae4814f2dc416d91c09fdd387931c99。

v60增加独立持久化采集日志：collector核对/sheng-persistent/hmos-compat/identity的精确两行后，在同目录创建0600 probe-BOOTID.log，写初始history并每秒fsync，上限16MiB。解决此前metadata采集unavailable导致重启证据丢失。v60已实刷，Probe SHA4031763a59833df55502fb12d8102b0e68c1a8c90da29f58a22dc2726e997fe4，boot_id68122793-bde6-4568-9ffa-52dd5b52f051；01:44已ipc成功→hmos，samgr/hilogd/coredeps/storage/sdc ret0/账户/appspawn/主题启动；后台hilog用setsid并在worker退出前sleep1保证脱离进程组。持久化collector日志已实际创建约1MiB。下一步启动GPU/RS/installs/foundation，核对sceneboard maps和WiFi等待是否消失，再追真实UI/物理出图。尚未桌面验收，尚未成功系统截图。

每轮日志归档均逐成员读取通过：
{chr(10).join(lines)}

真实userdata仅/data/hmos-compat普通镜像和独立调试文件；原内容和原机启动备份保留。vendor/vendor_dlkm不改不覆盖。无commit/push、无委派、无新定时任务；摄像头未开启。额度工具不可用，不能声称已查百分比。用户要求目标完成前持续推进。
'''
for n in ['analysis/续接检查点.md','analysis/轮次总结.md','analysis/20261027续接进展.md']:
 p=r/n;p.write_text(body+'\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
(r/'当前状态.md').write_text('# 当前移植状态\n\n'+body,encoding='utf-8')
print(body.splitlines()[0])
