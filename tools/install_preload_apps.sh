#!/busybox sh
# Explicit repair of existing userdata; not a per-boot reinstall policy.
set -eu
B=/busybox
R=/hmos-root
D=$R/data/local/tmp/preload-install-v97
L=$R/data/local/tmp/sheng-preload-install.lock
$B mkdir "$L" || { echo PRELOAD_OTHER_BATCH_EXISTS; exit 20; }
trap '$B rmdir "$L"' EXIT
$B mkdir -p "$D"
for name in ZhimuyunHm XiaoyuanAIHm ZuoyebangHm XunleiHm XiaohongshuHm IqiyiHm DouyinHm KuaiShouHm MeituxiuxiuHm ZwcadHm MindmasterHm CapCutHm WPSHm; do
 state=$($B chroot "$R" /system/bin/param get startup.service.ctl.sheng_bundle_cli | $B tr -d '[:space:]')
 [ "$state" = 5 ] || { echo "PRELOAD_CLIENT_BUSY state=$state"; exit 21; }
 echo "PRELOAD_BEGIN=$name"
 printf 'install %s\n' "$name" > "$R/data/local/tmp/sheng-bundle-request.txt"
 $B chmod 0644 "$R/data/local/tmp/sheng-bundle-request.txt"
 $B chroot "$R" /system/bin/param set sheng.debug.bundle.cli true
 i=0
 while :; do
  $B sleep 2
  state=$($B chroot "$R" /system/bin/param get startup.service.ctl.sheng_bundle_cli | $B tr -d '[:space:]')
  if [ "$state" = 5 ] && $B grep -q "name=$name" "$R/data/local/tmp/sheng-bundle-last.log"; then break; fi
  i=$((i+1)); [ "$i" -lt 125 ] || { echo "PRELOAD_TIMEOUT=$name"; exit 22; }
 done
 $B cp "$R/data/local/tmp/sheng-bundle-last.log" "$D/$name.log"
 $B cat "$D/$name.log"
 if $B grep -qx 'install bundle successfully.' "$D/$name.log"; then
  echo "PRELOAD_INSTALL_OK=$name"
 else
  echo "PRELOAD_INSTALL_FAILED=$name"
  exit 23
 fi
done
echo PRELOAD_BATCH_COMPLETE=1
