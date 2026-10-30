param([Parameter(Mandatory=$true)][ValidatePattern('^v[1-9][0-9]*$')][string]$Version)
. (Join-Path $PSScriptRoot 'Common.ps1')
$device=Select-Device fastboot 'YOUR_DEVICE_SERIAL'
if ((Get-FastbootVar $device product) -ne 'sheng') { throw 'Wrong product' }
$slot=Get-FastbootVar $device current-slot
if ($slot -ne 'a') { throw 'Only the tested A slot is supported' }
$backupFolder=Get-BackupFolder $device $slot
$backup=Get-Content -Raw -LiteralPath (Join-Path $backupFolder 'backup-manifest.json') | ConvertFrom-Json
if ($backup.Serial -ne $device -or $backup.Slot -ne $slot -or $backup.Files.Count -ne 3) { throw 'Backup manifest mismatch' }
foreach ($f in $backup.Files) { Assert-FileHash (Join-Path $backupFolder $f.File) $f.Sha256 }
$name='init_boot_hmos_probe_'+$Version+'.img'
$manifest=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot ($Version+'-manifest.json')) | ConvertFrom-Json
$entry=$manifest.('output/'+$name)
if (-not $entry) { $entry=$manifest.('output\'+$name) }
if (-not $entry.Sha256) { throw 'Image hash not recorded' }
$verified=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot ('../analysis/'+$Version+'-image-verification.json')) | ConvertFrom-Json
if (-not $verified.probe.cpio_verified -or -not $verified.probe.original_init_preserved -or $verified.probe.sha256 -ne $entry.Sha256) { throw 'Image verification mismatch' }
$path=Join-Path $PSScriptRoot $name
Assert-FileHash $path $entry.Sha256
if ((Get-Item -LiteralPath $path).Length -ne 8388608) { throw 'Wrong image size' }
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'flash','init_boot_a',$path))
# Our minimal HMOS boot has no Android boot-control service. Reset the tested
# current slot's retry counter before booting; never select the other slot.
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'set_active',$slot))
$receipt=[ordered]@{Time=(Get-Date -Format o);Serial=$device;Slot=$slot;Version=$Version;Mode='Probe';Files=@([ordered]@{Partition='init_boot_a';File=$name;Sha256=$entry.Sha256});Preserved='Existing boot_a and vendor_boot_a';CurrentSlotRetryCounterReset=$true}
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot ('logs/flash-receipt-'+$Version+'-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')) -Encoding UTF8
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'reboot'))
