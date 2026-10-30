from pathlib import Path
from datetime import datetime
import json
r=Path(__file__).resolve().parent.parent;t=datetime.now().astimezone().isoformat(timespec='seconds')
body=f'''## {t} v53 软件账户摘要实测；v54 存储服务候选

用户要求先真实桌面，TEE暂缓，并允许软件HUKS/成功返回路线。当前AnyHarmonyOS参考仓库明确不含软件HUKS，因此本轮独立实现仅账户别名 os_account_info_encryption_key 的软件HMAC；原参数构建仍复用原hukssdk，实际计算使用原OpenSSL，其他别名/句柄转交原实现。不是空摘要、假账户集合，也未宣称原TEE恢复。库持久收在init_boot，启动仅accountmgr设置LD_PRELOAD至/compat；vendor不改不遮蔽。

v51真机标准RFC4231/原参数ABI/密钥保存/分段输出/已结束句柄拒绝合约通过。v52误用原包库的根目录别名，SHA门控在启动原init前拒绝；已用v53修正为chipset-sdk和chipset-sdk-sp实际路径。v52不是账户失败或内核失败。

v53已冷刷，SHA f80d610182cd1faae69d9c6f6264f84807eb1a639dbd4bc7c8487ae09d1a623b。原accountmgr UID3058 PID409实际加载/compat/lib64/libsheng_account_hmac.so，创建0600随机开发密钥、账户摘要/列表，发布SA200 result0。原appspawn411/438已启动但未孵化应用。GPU模块、原RenderService494、installs496、foundation534已启动；原BMS日志register to sam success，账户收到SA401上线通知；不把缺失的SAFWK单行Publish日志伪造为已有。原4607/501/180/182/3299实际发布。没有桌面或系统截图。

账户ready仍false，无默认用户100的account_info.json。源码OnAddSystemAbility明确要求isStorageReady_后才进入默认用户创建；目前原存储5003未纳入。KV服务1301也未启动，但不能把它当已确定的首要阻点。BMS前台账户查询错误由4194322变为4194349。数据仍RAM ext4，可写约1.4GiB，用量466MiB。

证据：output/logs/command-shell-20261027-234828-2b86203c3ddd.log（原SA200/真实摘要文件）；command-shell-20261027-234900-2edecabdf2ca.log（GPU/RS/基础SA）；command-shell-20261027-234926-73358d9d6275.log（BMS注册、SA401通知、映射）。完整压缩日志：v53-account-initial-20261027.txt.gz SHA a1846fea9b63fa0cadce376e0a4a99b21f8c7b24288d42309ef2b9d53ed53b5e；v53-progress-20261027.txt.gz SHA 6b095842b4b3c7e2ca271199e52bf65057d2f5f6e87fbae75c53a3da8bfcef42；v53-final-20261027.txt.gz SHA 51942bf817ca3bccb14421210f33500b2e77e79e25edb0ddf7ad7cca213863cd。

已请求回Recovery，须以实际ADB检测确认。v54仅离线构建/完整解包验证通过，未刷入：Probe SHA64eb0c4a66cc122a3e7df8e512829b6f7d58dda048b78f01bdcee6da7e932b1d。新增独立/compat/etc/init-desktop-services.cfg，原storage_manager/storage_daemon/distributeddata显式门控，保留身份权限。daemon入口附加seccomp禁止新建任何块设备，真实userdata不暴露；不执行原分区挂载/格式化任务。下轮先原存储服务→账户创建→真实appspawn/SceneBoard；不重复方块、Binder或GPU合约。

无commit/push、无摄像头、无新自动任务；数值额度工具不可用，停止前必须回TWRP并导出记录。
'''
for name in ['analysis/续接检查点.md','analysis/轮次总结.md','analysis/20261027续接进展.md']:
    p=r/name;p.write_text(body+'\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
(r/'当前状态.md').write_text('# 当前移植状态\n\n'+body,encoding='utf-8')
p=r/'analysis/v53-framework.json';a=json.loads(p.read_text());a.update(status='FLASHED_ACCOUNT_HMAC_SA200_BMS_REGISTERED_STORAGE_MISSING',account_ready=False,account_uid=3058,account_pid=409,hmac_loaded=True,bms_registered=True,desktop=False,evidence=['output/logs/command-shell-20261027-234828-2b86203c3ddd.log','output/logs/command-shell-20261027-234926-73358d9d6275.log']);p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(t)
