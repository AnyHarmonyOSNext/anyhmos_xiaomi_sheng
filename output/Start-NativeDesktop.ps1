param(
    [Parameter(Mandatory=$true)][ValidatePattern('^v[1-9][0-9]*$')][string]$Version,
    [switch]$StartLocation
)
$ErrorActionPreference = 'Stop'
function Invoke-NativeStep([string]$Script,[int]$Seconds=12) {
    $r=(& (Join-Path $PSScriptRoot 'Invoke-ProbeCommand.ps1') -Script $Script -Seconds $Seconds) | ConvertFrom-Json
    $log=Get-Content -LiteralPath $r.Log -Raw -Encoding UTF8
    if(-not $r.Completed -or $log -notmatch ('CMD END id='+$r.Id+'\b[^\r\n]*exit=0 signal=0')) {
        throw ('Native startup step failed or remains in progress. Inspect before retrying: '+$r.Log)
    }
    Write-Host ('Verified startup step: '+$r.Log)
}
$core=@'
set -e
B=/busybox
R=/hmos-root
$B grep -q '^sheng_hmos_ipc ' /proc/modules
i=0
while ! $B test -S $R/dev/unix/socket/hilogInput; do
 i=$((i+1)); [ "$i" -lt 35 ] || exit 21; $B sleep 1
done
for gate in coredeps storaged; do $B chroot $R /system/bin/param set sheng.debug.start.$gate true; done
$B sleep 2
result=$($B chroot $R /system/bin/sdc filecrypt init_main_user)
echo "$result"
echo "$result" | $B grep -q 'ret: 0'
for gate in storage kvdata __USERIAM_GATE__ account appspawn theme wallpaper ui; do
 $B chroot $R /system/bin/param set sheng.debug.start.$gate true
done
$B setsid $B timeout 600 $B chroot $R /system/bin/hilog -L I,W,E,F > $R/data/local/tmp/__VERSION__-live.txt 2>&1 </dev/null &
$B sleep 1
'@
$useriamGate=if([int]$Version.Substring(1) -ge 73){'useriam'}else{''}
Invoke-NativeStep ($core.Replace('__VERSION__',$Version).Replace('__USERIAM_GATE__',$useriamGate)) 45
if([int]$Version.Substring(1) -ge 76) {
    # Configuration clients need the real distributed database service ready.
    $databaseReady=$false
    $databaseDeadline=[DateTime]::UtcNow.AddSeconds(90)
    while([DateTime]::UtcNow -lt $databaseDeadline) {
        $nonce=[guid]::NewGuid().ToString('N').Substring(0,12)
        $query='/busybox timeout 3 /busybox chroot /hmos-root /data/local/tmp/native_sa_dump 1301 /data/local/tmp/database-ready-'+$nonce+'.txt -l'
        $r=(& (Join-Path $PSScriptRoot 'Invoke-ProbeCommand.ps1') -Script $query -Seconds 6)|ConvertFrom-Json
        $log=Get-Content -LiteralPath $r.Log -Raw -Encoding UTF8
        if(-not $r.Completed) {throw ('Database readiness query incomplete; inspect '+$r.Log)}
        if($log -match ('CMD END id='+$r.Id+'\b[^\r\n]*exit=0 signal=0')) {
            $databaseReady=$true
            Write-Host ('Original database SA1301 ready: '+$r.Log)
            break
        }
        Start-Sleep -Seconds 1
    }
    if(-not $databaseReady){throw 'Original database SA1301 not ready within 90 seconds; inspect logs before restarting services.'}
}
if($StartLocation) {
    Invoke-NativeStep '/busybox chroot /hmos-root /system/bin/param set sheng.debug.start.location true'
}
Invoke-NativeStep (Get-Content -Raw (Join-Path $PSScriptRoot 'v49-native-graphics-installs-start.sh'))
if([int]$Version.Substring(1) -ge 78) {
    $touch=@'
set -e
B=/busybox
R=/hmos-root
$B chroot $R /system/bin/param set sheng.debug.start.touch true
i=0
while ! $B grep -q THP_INPUT_NODE_READY $R/data/local/tmp/sheng-thp-service.txt; do
 i=$((i+1)); [ "$i" -lt 18 ] || exit 31; $B sleep 1
done
$B head -n 4 $R/data/local/tmp/sheng-thp-service.txt
'@
    Invoke-NativeStep $touch 23
}
if([int]$Version.Substring(1) -ge 70) {
    Invoke-NativeStep '/busybox chroot /hmos-root /system/bin/param set sheng.debug.start.input true'
}
Invoke-NativeStep 'set -e; B=/busybox; R=/hmos-root; $B cp $R/data/local/tmp/foundation-app-core.json $R/system/profile/foundation.json; $B chroot $R /system/bin/param set sheng.debug.start.screen true; $B cat /proc/sys/kernel/random/boot_id /proc/uptime'
if([int]$Version.Substring(1) -ge 76) {
    Invoke-NativeStep '/busybox chroot /hmos-root /system/bin/param set sheng.debug.start.compconfig true'
}
if([int]$Version.Substring(1) -ge 73) {
    $waitScene=@'
set -e
B=/busybox
R=/hmos-root
p=/data/local/tmp/display-ready-__NONCE__.txt
if $B timeout 2 $B chroot $R /data/local/tmp/native_sa_dump 4606 "$p" -a && $B grep -qE 'SCBScreenLock|SCBDesktop' "$R$p"; then
 echo SCENE_WINDOW_READY=true
 $B chroot $R /system/bin/param set sheng.debug.display.wake true
else
 echo SCENE_WINDOW_READY=false
fi
'@
    $ready=$false
    $deadline=[DateTime]::UtcNow.AddSeconds(120)
    while([DateTime]::UtcNow -lt $deadline) {
        $nonce=[guid]::NewGuid().ToString('N').Substring(0,12)
        $r=(& (Join-Path $PSScriptRoot 'Invoke-ProbeCommand.ps1') -Script $waitScene.Replace('__NONCE__',$nonce) -Seconds 8)|ConvertFrom-Json
        $log=Get-Content -LiteralPath $r.Log -Raw -Encoding UTF8
        if(-not $r.Completed -or $log -notmatch ('CMD END id='+$r.Id+'\b[^\r\n]*exit=0 signal=0')) {throw ('Scene readiness query failed; inspect '+$r.Log)}
        if($log -match 'SCENE_WINDOW_READY=true') {$ready=$true; Write-Host ('Scene ready; wake requested: '+$r.Log); break}
        Start-Sleep -Seconds 2
    }
    if(-not $ready){throw 'Scene windows did not become ready within 120 seconds; inspect logs before restarting any service.'}
} elseif([int]$Version.Substring(1) -ge 72) {
    Invoke-NativeStep '/busybox sleep 6; /busybox chroot /hmos-root /system/bin/param set sheng.debug.display.wake true' 12
}
if([int]$Version.Substring(1) -ge 78) {
    $unlock=@'
set -e
B=/busybox
R=/hmos-root
$B chroot $R /system/bin/param set sheng.debug.screen.unlock true
$B sleep 10
$B cat $R/data/local/tmp/sheng-capture/unlock-request.txt
$B grep -q 'after=0' $R/data/local/tmp/sheng-capture/unlock-request.txt
'@
    Invoke-NativeStep $unlock 15
}
Write-Host 'Native desktop services requested. Desktop, screenshots and physical display still require verification.'
