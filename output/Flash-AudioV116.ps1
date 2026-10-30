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
$vp=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../analysis/vendor-boot-audio-v116-verification.json') -Raw | ConvertFrom-Json
$ip=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../analysis/v116-image-verification.json') -Raw | ConvertFrom-Json
if (-not $vp.preserved_original_entries -or -not $vp.dtb_unchanged -or -not $vp.bootconfig_unchanged -or -not $ip.probe.cpio_verified) { throw 'Offline validation missing' }
$vb=Join-Path $PSScriptRoot 'vendor_boot_hmos_audio_v116.img'
$ib=Join-Path $PSScriptRoot 'init_boot_hmos_probe_v116.img'
Assert-FileHash $vb $vp.sha256
Assert-FileHash $ib $ip.probe.sha256
if ((Get-Item -LiteralPath $vb).Length -ne 100663296 -or (Get-Item -LiteralPath $ib).Length -ne 8388608) { throw 'Image size mismatch' }
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'flash','vendor_boot_a',$vb))
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'flash','init_boot_a',$ib))
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'set_active','a'))
$receipt=[ordered]@{Time=(Get-Date -Format o);Serial=$device;Slot='a';Version='v116';Files=@(@{Partition='vendor_boot_a';Sha256=$vp.sha256},@{Partition='init_boot_a';Sha256=$ip.probe.sha256});Preserved='boot_a, vendor, vendor_dlkm, super, userdata';ReadbackVerified=$false}
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot ('logs/flash-receipt-v116-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')) -Encoding UTF8
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'reboot'))
