$ErrorActionPreference = 'Stop'
$Fastboot = Join-Path $PSScriptRoot 'platform-tools\fastboot.exe'
$Adb = Join-Path $PSScriptRoot 'platform-tools\adb.exe'

function Invoke-DeviceTool {
    param([string]$Tool, [string[]]$ToolArgs)
    $lines = @(& $Tool @ToolArgs 2>&1 | ForEach-Object { "$_" })
    $code = $LASTEXITCODE
    [pscustomobject]@{ Code = $code; Text = ($lines -join "`n") }
}
function Require-Success {
    param($Result)
    Write-Host $Result.Text
    if ($Result.Code -ne 0) { throw "Device command failed (exit $($Result.Code)); stopped." }
}
function Get-FastbootVar {
    param([string]$DeviceSerial, [string]$Name)
    $r = Invoke-DeviceTool $Fastboot @('-s', $DeviceSerial, 'getvar', $Name)
    if ($r.Code -ne 0) { throw $r.Text }
    $m = [regex]::Match($r.Text, '(?m)^(?:\(bootloader\)\s*)?' + [regex]::Escape($Name) + ':\s*(\S+)')
    if (-not $m.Success) { throw "Cannot read fastboot variable $Name : $($r.Text)" }
    $m.Groups[1].Value
}
function Select-Device {
    param([ValidateSet('adb', 'fastboot')][string]$Mode, [string]$RequestedSerial)
    if ($Mode -eq 'adb') {
        $r = Invoke-DeviceTool $Adb @('devices')
        $devices = @([regex]::Matches($r.Text, '(?m)^(\S+)\s+(?:device|recovery)\s*$') | ForEach-Object { $_.Groups[1].Value })
    } else {
        $r = Invoke-DeviceTool $Fastboot @('devices')
        $devices = @([regex]::Matches($r.Text, '(?m)^(\S+)\s+fastboot\s*$') | ForEach-Object { $_.Groups[1].Value })
    }
    if ($r.Code -ne 0) { throw $r.Text }
    if ($RequestedSerial) {
        if ($devices -notcontains $RequestedSerial) { throw "Requested device $RequestedSerial is not connected in $Mode mode." }
        return $RequestedSerial
    }
    if ($devices.Count -ne 1) { throw "Expected one $Mode device, found $($devices.Count). Connect it, or specify -Serial." }
    $devices[0]
}
function Assert-FileHash {
    param([string]$Path, [string]$Sha256)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing file: $Path" }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Sha256) { throw "SHA256 mismatch: $Path" }
}
function Get-BackupFolder {
    param([string]$DeviceSerial, [string]$Slot)
    if ($DeviceSerial -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid device serial for backup path.' }
    Join-Path $PSScriptRoot "device-backup\$DeviceSerial\$Slot"
}
