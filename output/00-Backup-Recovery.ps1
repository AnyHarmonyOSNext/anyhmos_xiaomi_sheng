param([string]$Serial, [ValidateSet('a','b')][string]$Slot)
. (Join-Path $PSScriptRoot 'Common.ps1')
$device = Select-Device 'adb' $Serial
$id = Invoke-DeviceTool $Adb @('-s', $device, 'shell', 'id')
if ($id.Code -ne 0 -or $id.Text -notmatch 'uid=0') { throw 'Run this from a root-enabled Recovery with ADB.' }
if (-not $Slot) {
    $r = Invoke-DeviceTool $Adb @('-s', $device, 'shell', 'getprop ro.boot.slot_suffix')
    if ($r.Text.Trim() -match '^_([ab])$') { $Slot = $Matches[1] }
    else { throw 'Recovery does not report the active slot. Check it in fastboot, then pass -Slot a or -Slot b.' }
}
$dest = Get-BackupFolder $device $Slot
if (Test-Path -LiteralPath $dest) { throw "Backup folder already exists; preserve it before creating another: $dest" }
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$files = @()
foreach ($name in @('boot','init_boot','vendor_boot')) {
    $part = "${name}_$Slot"
    $tmp = "/tmp/hmos-backup-$part.img"
    $r = Invoke-DeviceTool $Adb @('-s', $device, 'shell', "dd if=/dev/block/by-name/$part of=$tmp bs=1048576")
    Require-Success $r
    $local = Join-Path $dest "$part.img"
    Require-Success (Invoke-DeviceTool $Adb @('-s', $device, 'pull', $tmp, $local))
    $length = (Get-Item -LiteralPath $local).Length
    if ($length -lt 4096) { throw "Backup is too small: $local" }
    $files += [pscustomobject]@{ Partition = $part; File = "$part.img"; Bytes = $length; Sha256 = (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash }
    Require-Success (Invoke-DeviceTool $Adb @('-s', $device, 'shell', "rm -f $tmp"))
}
[pscustomobject]@{ Serial = $device; Slot = $Slot; Created = (Get-Date).ToString('o'); Files = $files } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $dest 'backup-manifest.json') -Encoding UTF8
Write-Host "Backup complete: $dest. Review the matching image and backup hashes before any flash operation."
