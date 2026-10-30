param([string]$Serial='YOUR_DEVICE_SERIAL')
. (Join-Path $PSScriptRoot 'Common.ps1')
$device=Select-Device fastboot $Serial
if ((Get-FastbootVar $device product) -ne 'sheng') { throw 'Wrong product' }
$slot=Get-FastbootVar $device current-slot
if ($slot -ne 'a') { throw 'Only tested slot a supported' }
$folder=Get-BackupFolder $device $slot
$backup=Get-Content -LiteralPath (Join-Path $folder 'backup-manifest.json') -Raw | ConvertFrom-Json
if ($backup.Serial -ne $device -or $backup.Slot -ne $slot -or $backup.Files.Count -ne 3) { throw 'Backup manifest mismatch' }
foreach ($f in $backup.Files) { Assert-FileHash (Join-Path $folder $f.File) $f.Sha256 }
$v=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../analysis/vendor-migration-v117-verification.json') -Raw | ConvertFrom-Json
if (-not $v.cpio_verified -or -not $v.preserved_original_entries -or -not $v.preserved_v116_audio -or -not $v.dtb_unchanged -or -not $v.bootconfig_unchanged -or $v.generic_entry_bytes -gt 16384) { throw 'Offline validation missing' }
foreach ($item in @($v.vendor_boot,$v.init_boot)) {
    $path=Join-Path $PSScriptRoot $item.file
    Assert-FileHash $path $item.sha256
    if ((Get-Item -LiteralPath $path).Length -ne $item.bytes) { throw 'Image size mismatch' }
}
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'flash','vendor_boot_a',(Join-Path $PSScriptRoot $v.vendor_boot.file)))
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'flash','init_boot_a',(Join-Path $PSScriptRoot $v.init_boot.file)))
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'set_active','a'))
$receipt=[ordered]@{Time=(Get-Date -Format o);Serial=$device;Slot='a';Version='v117';Files=@(@{Partition='vendor_boot_a';Sha256=$v.vendor_boot.sha256},@{Partition='init_boot_a';Sha256=$v.init_boot.sha256});Preserved='boot_a, vendor, vendor_dlkm, super, userdata';ReadbackVerified=$false}
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot ('logs/flash-receipt-v117-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')) -Encoding UTF8
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'reboot'))
