param([string]$Serial)
. (Join-Path $PSScriptRoot 'Common.ps1')
$device = Select-Device 'adb' $Serial
$id = Invoke-DeviceTool $Adb @('-s', $device, 'shell', 'id')
if ($id.Code -ne 0 -or $id.Text -notmatch 'uid=0') { throw 'Root-enabled Recovery ADB is required.' }
$mounts = Invoke-DeviceTool $Adb @('-s', $device, 'shell', 'cat /proc/mounts')
if ($mounts.Text -notmatch '\s/metadata\s') {
    $mountCommand = 'mkdir -p /metadata; mount /metadata || mount -t f2fs -o nosuid,nodev,noatime /dev/block/by-name/metadata /metadata || mount -t mifs -o nosuid,nodev,noatime /dev/block/by-name/metadata /metadata || mount -t ext4 -o nosuid,nodev,noatime /dev/block/by-name/metadata /metadata'
    Require-Success (Invoke-DeviceTool $Adb @('-s', $device, 'shell', $mountCommand))
}
$check = Invoke-DeviceTool $Adb @('-s', $device, 'shell', 'ls /metadata/hmos-debug/probe-*.log')
if ($check.Code -ne 0) { throw 'No probe logs found. Save USB serial output; report whether the device restarted and whether a COM port appeared.' }
$dest = Join-Path $PSScriptRoot ('logs\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $dest -Force | Out-Null
foreach ($remote in ($check.Text -split "`r?`n")) {
    $remote = $remote.Trim()
    if ($remote -notmatch '^/metadata/hmos-debug/probe-[a-f0-9-]+\.log$') { continue }
    $path = Join-Path $dest ([System.IO.Path]::GetFileName($remote))
    # Stream bytes via .NET: some Windows adb builds truncate Unicode folder
    # names during recursive adb pull.
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Adb
    $info.Arguments = "-s $device exec-out cat $remote"
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::Start($info)
    $stream = [System.IO.File]::Create($path)
    try { $process.StandardOutput.BaseStream.CopyTo($stream) } finally { $stream.Dispose() }
    $errorText = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    $code = $process.ExitCode
    $process.Dispose()
    if ($code -ne 0) { throw "Log export failed: $errorText" }
    Write-Host "Saved $path"
}
(Invoke-DeviceTool $Adb @('-s', $device, 'shell', 'cat /proc/mounts')).Text | Set-Content -LiteralPath (Join-Path $dest 'recovery-mounts.txt') -Encoding UTF8
Write-Host "Logs saved: $dest"
