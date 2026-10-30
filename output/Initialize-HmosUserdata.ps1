param([string]$Serial='YOUR_DEVICE_SERIAL', [ValidatePattern('^v[1-9][0-9]*$')][string]$Version='v95', [switch]$EraseUserdata)
. (Join-Path $PSScriptRoot 'Common.ps1')
if (-not $EraseUserdata) { throw 'This command clears all userdata. Explicitly pass -EraseUserdata for a clean installation.' }
$device = Select-Device 'adb' $Serial
if ($device -ne 'YOUR_DEVICE_SERIAL') { throw 'This layout package is provisioned for YOUR_DEVICE_SERIAL only.' }
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'userdata-layout-v1.json') -Raw | ConvertFrom-Json
$script = Join-Path $PSScriptRoot 'provision-userdata-v93.sh'
$busybox = Join-Path $PSScriptRoot '../compat/debug-tools/busybox-aarch64'
Assert-FileHash $script $manifest.ProvisionSha256
Assert-FileHash $busybox $manifest.BusyboxSha256
if ([int]$Version.Substring(1) -lt 94) { throw 'A clean installation requires v94 or later for first-boot directory initialization.' }
$verified = Get-Content -LiteralPath (Join-Path $PSScriptRoot ("../analysis/$Version-image-verification.json")) -Raw | ConvertFrom-Json
if (-not $verified.probe.cpio_verified) { throw 'Verified direct-mount boot package is missing.' }
Assert-FileHash (Join-Path $PSScriptRoot ("init_boot_hmos_probe_$Version.img")) $verified.probe.sha256
Require-Success (Invoke-DeviceTool $Adb @('-s',$device,'push',$busybox,'/tmp/busybox'))
Require-Success (Invoke-DeviceTool $Adb @('-s',$device,'shell','chmod 0755 /tmp/busybox'))
Require-Success (Invoke-DeviceTool $Adb @('-s',$device,'push',$script,'/tmp/provision-userdata-v93.sh'))
$result = Invoke-DeviceTool $Adb @('-s',$device,'shell','sh /tmp/provision-userdata-v93.sh')
$log = Join-Path $PSScriptRoot ('logs/userdata-provision-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.txt')
$result.Text | Set-Content -LiteralPath $log -Encoding UTF8
Require-Success $result
if ($result.Text -notmatch 'HMOS_WHOLE_USERDATA_FRESH_PROVISIONED_NO_OLD_DATA_RESTORED') { throw "Missing completion marker; inspect $log" }
Write-Host "Fresh whole userdata is ready. Flash the verified $Version boot package before starting HarmonyOS."
