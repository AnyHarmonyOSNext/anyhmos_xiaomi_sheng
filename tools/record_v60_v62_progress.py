from pathlib import Path
from datetime import datetime
import hashlib,tarfile
r=Path(__file__).resolve().parent.parent
arcs=[]
for n in ['v60-persistent-20261028-015023.tar','v61-persistent-20261028-015418.tar']:
 p=r/'output/logs'/n
 with tarfile.open(p) as t:
  for m in t.getmembers():assert m.isfile() and len(t.extractfile(m).read())==m.size
 arcs.append(f'- output/logs/{n}: {p.stat().st_size} bytes, SHA256 {hashlib.sha256(p.read_bytes()).hexdigest()}')
body=f'''## {datetime.now().astimezone().isoformat(timespec='seconds')} v60/v61 已测收档，v62 实刷进行中

v60实测：账户ready/SceneBoard863真实孵化，独立UI LoadWifiSa桥映射到appspawn及SceneBoard；减少加载等待，但原SDK忽略其返回值，随后GetSystemAbility仍同步重试2秒以上，SceneBoard反复THREAD_BLOCK_6S。不能称此桥解决WiFi阻塞。v60发生非主动重启，持久化collector日志保留到uptime262.665秒，最后仅正常SAMGR/IPC信息，没有reboot/panic/fatal直接证据；随后新bootHOLD61秒。几轮都在数分钟后重启，根因未定。oops SHA仍abc3dfa1c87e5b9fc0a9e7eeaee5471d4fb61eef6eb76a5b9145d780bb2bec61，与旧轮相同，无新panic记录。Recovery中无/dev/watchdog或sysfs watchdog设备，不据此断言不存在所有内核/固件watchdog。

独立持久日志已真正取回：output/logs/persistent-probe-68122793-bde6-4568-9ffa-52dd5b52f051.log，1552408 bytes，SHA f728dffb4ed1f34850cf80ff1d5103a03d42dbcb36121cb50acb118d7eeaae12。v61 runtime日志352b303d-0cc2-49ec-8267-9ec485b226ed，1681437 bytes，SHA3da7b1016e24bdcee32a087fe03497658cff47ce9f6dce5e67bd670a0e54159c。tools/collect_runtime_logs.py可在Recovery再次导出。

v61实刷SHA831aaf5d181fe763e25b32029cf1cf12ea5b855188b7da27fd883a01b94cd7c4：原WiFi SDK隐藏GetWifiDeviceProxy入口VA0x4e628改mov w0,0;ret；调用者0x49c88/0x4e548对0走失败分支，没有伪造联网成功。输入SHA06765b1a54ac5c861baf5902f9081bb7da93a3b6765ae53085e150d3d7a00368、补丁输出SHAe5acdc59bdf38e17d19110863acd015373a081835f6c3c5ab8c7e94643e4a13f；analysis/v61-wifi-unavailable-patch.json记载ELF段换算与精确字节。兼容文件仅放/compat/lib64。实际SceneBoard904仍映射原/system路径SDK，应用namespace未采用全局搜索前缀，所以本轮补丁未对应用生效，仍冻结。原loader对兼容SDK依赖解析全部通过。截图本轮触发但未取回查看，不宣称有内容。uptime136秒主动回TWRP成功，未发生该轮自动重启，也不重复等待它。

v62仅改appspawn原init服务LD_PRELOAD=/compat/lib64/libwifi_sdk.z.so，保证在应用namespace构造前加载；不再使用旧的LoadWifiSa窄桥。已构建/完整解包验证、实刷，Probe SHA92ec4bcba05d3a8649ca19e35239280987519870166678e25e70f861139da1e7。01:55已ipc→hmos、存储/sdc ret0、账户/appspawn/主题、GPU/原RS/installs/foundation启动，后台有界hilog写/data/local/tmp/v62-live.txt。下一步必须核对应用maps是否选中compat SDK、WiFi调用耗时/冻结是否解除，再追窗口内容和显示；仍无真实桌面验收。

两轮原始日志归档逐成员读取验证：
{chr(10).join(arcs)}

全部兼容处理独立/compat，vendor不改不覆盖，原包/原userdata内容/启动分区备份保留。无commit/push、无委派、无定时任务；摄像头关闭。状态为继续工作，非完成。
'''
for n in ['analysis/续接检查点.md','analysis/轮次总结.md','analysis/20261027续接进展.md']:
 p=r/n;p.write_text(body+'\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
(r/'当前状态.md').write_text('# 当前移植状态\n\n'+body,encoding='utf-8')
print(body.splitlines()[0])
