param([string]$Serial='YOUR_DEVICE_SERIAL')
. (Join-Path $PSScriptRoot 'Common.ps1')
$device=Select-Device fastboot $Serial
if ((Get-FastbootVar $device product) -ne 'sheng' -or (Get-FastbootVar $device current-slot) -ne 'a') { throw 'Wrong product or slot' }
$folder=Get-BackupFolder $device 'a'
$backup=Get-Content -LiteralPath (Join-Path $folder 'backup-manifest.json') -Raw | ConvertFrom-Json
if ($backup.Serial -ne $device -or $backup.Slot -ne 'a' -or $backup.Files.Count -ne 3) { throw 'Backup mismatch' }
foreach ($f in $backup.Files) { Assert-FileHash (Join-Path $folder $f.File) $f.Sha256 }
$v=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../analysis/zink-test-v125-verification.json') -Raw | ConvertFrom-Json
if ($v.version -ne 'v125' -or -not $v.cpio_verified -or -not $v.preserved_v124_entries -or -not $v.init_boot_unchanged -or -not $v.dtb_unchanged -or -not $v.bootconfig_unchanged -or -not $v.stock_vendor_modules_and_audio_unchanged) { throw 'Verification missing' }
$image=Join-Path $PSScriptRoot $v.vendor_boot.file
Assert-FileHash $image $v.vendor_boot.sha256
Assert-FileHash (Join-Path $PSScriptRoot 'init_boot_hmos_entry_v118.img') '6f3eb88aa1422f6ed114f58c0e32e991b01b9ab3fa96c386626434891e215ef9'
if ((Get-Item -LiteralPath $image).Length -ne 100663296) { throw 'Unexpected image size' }
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'flash','vendor_boot_a',$image))
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'set_active','a'))
$receipt=[ordered]@{Time=(Get-Date -Format o);Serial=$device;Slot='a';Version='v125';Partition='vendor_boot_a';Sha256=$v.vendor_boot.sha256;ReadbackVerified=$false;CurrentSlotRetryCounterReset=$true;Preserved='boot_a, init_boot_a(v118), vendor, vendor_dlkm, super, userdata'}
$receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot ('logs/flash-receipt-v125-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')) -Encoding UTF8
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'reboot'))
