param([string]$Serial)
. (Join-Path $PSScriptRoot 'Common.ps1')
$device = Select-Device 'fastboot' $Serial
if ((Get-FastbootVar $device 'product') -ne 'sheng') { throw 'Unexpected product.' }
$slot = Get-FastbootVar $device 'current-slot'
$folder = Get-BackupFolder $device $slot
$backup = Get-Content -LiteralPath (Join-Path $folder 'backup-manifest.json') -Raw | ConvertFrom-Json
if ($backup.Serial -ne $device -or $backup.Slot -ne $slot -or $backup.Files.Count -ne 3) { throw 'Device backup manifest does not match.' }
foreach ($f in $backup.Files) {
    if ($f.Partition -notin @("boot_$slot","init_boot_$slot","vendor_boot_$slot") -or $f.File -ne "$($f.Partition).img") { throw 'Invalid backup entry.' }
    Assert-FileHash (Join-Path $folder $f.File) $f.Sha256
}
foreach ($f in $backup.Files) { Require-Success (Invoke-DeviceTool $Fastboot @('-s', $device, 'flash', $f.Partition, (Join-Path $folder $f.File))) }
Write-Host 'Original boot chain restored. The HMOS super is unchanged; restoring Android also requires the matching original super.'
