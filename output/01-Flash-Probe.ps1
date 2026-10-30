param([string]$Serial, [ValidateSet('Probe','Trace')][string]$Mode='Probe', [ValidatePattern('^v[1-9][0-9]*$')][string]$Version='v13', [ValidateSet('Auto','Stock303','ShengExports')][string]$Kernel='Auto')
. (Join-Path $PSScriptRoot 'Common.ps1')
if ($Kernel -eq 'Auto') {
    $Kernel = if ([int]$Version.Substring(1) -ge 16) { 'ShengExports' } else { 'Stock303' }
}
if ([int]$Version.Substring(1) -ge 16 -and $Kernel -ne 'ShengExports') {
    throw 'Probe v16 and later require the verified typed kernel API table. Stock303 cannot load their IPC module. No partitions were flashed; use ShengExports or 03-Restore-BootChain.ps1 for a full original restore.'
}
$device = Select-Device 'fastboot' $Serial
if ((Get-FastbootVar $device 'product') -ne 'sheng') { throw 'This package is only for sheng (Xiaomi Pad 6S Pro 12.4).' }
$slot = Get-FastbootVar $device 'current-slot'
if ($slot -ne 'a') { throw "Current slot is $slot. The supplied hmos super only contains A-slot data. No partitions were flashed." }
$backupFolder = Get-BackupFolder $device $slot
$backupPath = Join-Path $backupFolder 'backup-manifest.json'
if (-not (Test-Path -LiteralPath $backupPath)) { throw 'Back up the current boot chain in Recovery with 00-Backup-Recovery.ps1 first.' }
$backup = Get-Content -LiteralPath $backupPath -Raw | ConvertFrom-Json
if ($backup.Serial -ne $device -or $backup.Slot -ne $slot -or $backup.Files.Count -ne 3) { throw 'Device backup manifest does not match.' }
foreach ($f in $backup.Files) { Assert-FileHash (Join-Path $backupFolder $f.File) $f.Sha256 }
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'package-manifest.json') -Raw | ConvertFrom-Json
$initImage = 'init_boot_hmos_' + $Mode.ToLowerInvariant() + '_' + $Version + '.img'
$versionManifestPath = Join-Path $PSScriptRoot ($Version + '-manifest.json')
if (Test-Path -LiteralPath $versionManifestPath) {
    $versionManifest = Get-Content -LiteralPath $versionManifestPath -Raw | ConvertFrom-Json
    $entry = $versionManifest.('output/' + $initImage)
    if (-not $entry) { $entry = $versionManifest.('output\' + $initImage) }
    if (-not $entry.Sha256) { throw 'The version manifest does not contain the selected image.' }
    $manifest | Add-Member -MemberType NoteProperty -Name $initImage -Value $entry -Force
}
$jobs = @(@{Name='boot';File='boot_stock_303.img'},@{Name='vendor_boot';File='vendor_boot_stock_303.img'},@{Name='init_boot';File=$initImage})
if ($Kernel -eq 'ShengExports') {
    if ([int]$Version.Substring(1) -lt 16) { throw 'The typed kernel API table requires Probe v16 or later.' }
    $kernelManifest=Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'kernel-sheng-exports-manifest.json') | ConvertFrom-Json
    if (-not $kernelManifest.compatibility.abi_verified -or -not $kernelManifest.compatibility.cfi_enabled) { throw 'Custom kernel ABI/CFI checks are missing.' }
    $jobs[0].File='boot_sheng_exports_303.img'
    $manifest | Add-Member -MemberType NoteProperty -Name $jobs[0].File -Value $kernelManifest.($jobs[0].File) -Force
}
foreach ($j in $jobs) { Assert-FileHash (Join-Path $PSScriptRoot $j.File) $manifest.($j.File).Sha256 }
foreach ($j in $jobs) {
    Write-Host "Flashing $($j.Name)_$slot using $($j.File)"
    Require-Success (Invoke-DeviceTool $Fastboot @('-s', $device, 'flash', "$($j.Name)_$slot", (Join-Path $PSScriptRoot $j.File)))
}
Require-Success (Invoke-DeviceTool $Fastboot @('-s',$device,'set_active',$slot))
$receipt = [ordered]@{ Time=(Get-Date -Format o); Serial=$device; Slot=$slot; Version=$Version; Mode=$Mode; Kernel=$Kernel; Files=@($jobs | ForEach-Object { [ordered]@{ Partition=($_.Name+'_'+$slot); File=$_.File; Sha256=$manifest.($_.File).Sha256 } }) }
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $PSScriptRoot ('logs/flash-receipt-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')) -Encoding UTF8
Require-Success (Invoke-DeviceTool $Fastboot @('-s', $device, 'reboot'))
if ($Mode -eq 'Probe' -and [int]$Version.Substring(1) -ge 79) { Write-Host 'Autonomous native startup installed. Observe the USB COM port; do not resend ipc/hmos or the host startup script while startup is running.' }
elseif ($Mode -eq 'Probe') { Write-Host 'Probe installed in diagnostic HOLD. Use the USB COM port for status, hmos-list, or hmos; collect metadata logs in Recovery when finished.' }
else { Write-Host 'Trace installed. It starts the preserved Android init after enabling logging; reboot loops may recur. Enter Recovery and run 02-Collect-Recovery.ps1.' }
