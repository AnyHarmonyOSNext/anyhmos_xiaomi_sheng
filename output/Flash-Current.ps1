param([string]$Serial='YOUR_DEVICE_SERIAL')
. (Join-Path $PSScriptRoot 'Common.ps1')
$device=Select-Device fastboot $Serial
if ((Get-FastbootVar $device product) -ne 'sheng' -or (Get-FastbootVar $device current-slot) -ne 'a') { throw 'Wrong product or slot' }
$folder=Get-BackupFolder $device 'a'
$backup=Get-Content -LiteralPath (Join-Path $folder 'backup-manifest.json') -Raw | ConvertFrom-Json
if ($backup.Serial -ne $device -or $backup.Slot -ne 'a' -or $backup.Files.Count -ne 3) { throw 'Backup mismatch' }
foreach ($f in $backup.Files) { Assert-FileHash (Join-Path $folder $f.File) $f.Sha256 }
$v=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../analysis/userdata-ext4-fix-verification.json') -Raw | ConvertFrom-Json
if (-not $v.cpio_roundtrip_verified -or -not $v.unrelated_entries_unchanged -or -not $v.init_boot_unchanged -or -not $v.boot_unchanged -or -not $v.dtb_unchanged -or -not $v.bootconfig_unchanged -or -not $v.original_vendor_modules_unchanged -or -not $v.tests.aarch64_bootstrap_build -or $v.tests.disposable_loop_cases_passed -lt 11) { throw 'Verification missing' }
$image=Join-Path $PSScriptRoot $v.vendor_boot.file
Assert-FileHash $image $v.vendor_boot.sha256
Assert-FileHash (Join-Path $PSScriptRoot 'init_boot_hmos_entry_v118.img') '6f3eb88aa1422f6ed114f58c0e32e991b01b9ab3fa96c386626434891e215ef9'
if ((Get-Item -LiteralPath $image).Length -ne 100663296) { throw 'Unexpected image size' }
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'flash','vendor_boot_a',$image))
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'set_active','a'))
$receipt=[ordered]@{Time=(Get-Date -Format o);Serial=$device;Slot='a';Change='userdata-ext4';Partition='vendor_boot_a';Sha256=$v.vendor_boot.sha256;ReadbackVerified=$false;BootVerified=$false;CurrentSlotRetryCounterReset=$true;Preserved='boot_a, init_boot_a, super, userdata'}
$logFolder=Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
$receipt | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logFolder ('flash-receipt-userdata-ext4-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')) -Encoding UTF8
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'reboot'))
