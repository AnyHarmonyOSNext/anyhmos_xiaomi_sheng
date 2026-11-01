[CmdletBinding()]
param(
    [ValidateSet('Verify','Inspect','Flash')][string]$Mode = 'Verify',
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Serial,
    [string]$PackageRoot
)
$ErrorActionPreference = 'Stop'
if (!$PackageRoot) { $PackageRoot = [IO.Path]::GetDirectoryName($MyInvocation.MyCommand.Path) }
$PackageRoot = (Resolve-Path -LiteralPath $PackageRoot).Path
$Fastboot = Join-Path $PackageRoot 'bin\fastboot.exe'
$ManifestPath = Join-Path $PackageRoot 'PACKAGE.json'
if (!(Test-Path -LiteralPath $ManifestPath)) { throw 'PACKAGE.json is missing.' }
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
if ($Manifest.kind -ne 'sheng-promax-experimental' -or $Manifest.device_boot_tested -isnot [bool]) {
    throw 'Unexpected package identity or validation status.'
}
$RequiredImages = @('boot.img','init_boot.img','vendor_boot.img','vbmeta.img','vbmeta_system.img','super.img','userdata.img')
foreach ($Name in $RequiredImages) {
    $Records = @($Manifest.files | Where-Object { $_.path -eq "images/$Name" })
    if ($Records.Count -ne 1) { throw "Missing or duplicate artifact: $Name" }
}
Write-Host 'Verifying package sizes and SHA-256 checksums...'
# 刷写前逐项核对文件大小和哈希
foreach ($Record in $Manifest.files) {
    if ($Record.path -match '(^[\\/]|:|(^|[\\/])\.\.([\\/]|$))') { throw 'Invalid manifest path.' }
    $Path = Join-Path $PackageRoot $Record.path
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing file: $($Record.path)" }
    if ((Get-Item -LiteralPath $Path).Length -ne [long]$Record.bytes) { throw "Size mismatch: $($Record.path)" }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Record.sha256) {
        throw "SHA-256 mismatch: $($Record.path)"
    }
    Write-Host "Verified $($Record.path)"
}
Write-Host 'Experimental GEM-W00 207.0.0.111(SP12) port.'
if ($Manifest.device_boot_tested) {
    Write-Host 'A device boot was validated; see reports/device-validation.json for scope.'
} else {
    Write-Host 'Successful device boot has NOT been validated for this image.'
}
Write-Host ('Not validated: ' + (@($Manifest.not_validated) -join ', '))
if ($Mode -eq 'Verify') { Write-Host 'Offline verification passed. No device command was sent.'; return }

$LogDir = Join-Path $PackageRoot 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogPath = Join-Path $LogDir ('fastboot-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.txt')
# 同时读取标准输出和错误流，避免原生命令阻塞
function Invoke-Fastboot([string[]]$Arguments) {
    foreach ($Argument in $Arguments) {
        if ($Argument.Contains('"') -or $Argument.EndsWith('\')) { throw 'Unsupported native argument.' }
    }
    $Start = New-Object System.Diagnostics.ProcessStartInfo
    $Start.FileName = $Fastboot
    $Start.Arguments = (($Arguments | ForEach-Object { '"' + $_ + '"' }) -join ' ')
    $Start.UseShellExecute = $false
    $Start.CreateNoWindow = $true
    $Start.RedirectStandardOutput = $true
    $Start.RedirectStandardError = $true
    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $Start
    try {
        [void]$Process.Start()
        $Stdout = $Process.StandardOutput.ReadToEndAsync()
        $Stderr = $Process.StandardError.ReadToEndAsync()
        $Timeout = 30000
        if ($Arguments -contains 'flash') { $Timeout = 1800000 }
        if (!$Process.WaitForExit($Timeout)) {
            $Process.Kill()
            throw 'fastboot timed out. Check the USB connection before retrying.'
        }
        $Text = $Stdout.Result + "`n" + $Stderr.Result
        Add-Content -LiteralPath $LogPath -Value ("fastboot " + ($Arguments -join ' ') + "`n" + $Text)
        if ($Process.ExitCode -ne 0) { throw "fastboot failed ($($Process.ExitCode)):`n$Text" }
        return $Text
    } finally { $Process.Dispose() }
}
$Devices = Invoke-Fastboot @('devices')
$Found = @([regex]::Matches($Devices, '(?m)^([a-zA-Z0-9_-]+)\s+fastboot\s*$') | ForEach-Object { $_.Groups[1].Value })
if ($Serial) {
    if ($Found -notcontains $Serial) { throw 'Requested Fastboot serial is absent.' }
} else {
    if ($Found.Count -ne 1) { throw 'Connect exactly one Fastboot device, or specify -Serial.' }
    $Serial = $Found[0]
}
function Get-FastbootVar([string]$Name) {
    $Result = Invoke-Fastboot @('-s',$Serial,'getvar',$Name)
    $Match = [regex]::Match($Result, '(?m)^(?:\(bootloader\)\s*)?' + [regex]::Escape($Name) + ':\s*(\S+)\s*$')
    if (!$Match.Success) { throw "Cannot read Fastboot variable: $Name" }
    return $Match.Groups[1].Value
}
function Convert-HexSize([string]$Value) {
    if ($Value -notmatch '^0x[0-9a-fA-F]+$') { throw "Invalid partition size: $Value" }
    return [Convert]::ToInt64($Value.Substring(2),16)
}
# 核对设备型号、解锁状态及实际分区容量
if ((Get-FastbootVar 'product') -ne 'sheng') { throw 'Only Xiaomi sheng is supported.' }
if ((Get-FastbootVar 'unlocked') -ne 'yes') { throw 'Bootloader must already be unlocked.' }
if ((Get-FastbootVar 'is-userspace') -ne 'no') { throw 'Use bootloader Fastboot, not fastbootd.' }
if ((Get-FastbootVar 'current-slot') -notin @('a','b')) { throw 'Unexpected slot layout.' }
$SuperBytes = Convert-HexSize (Get-FastbootVar 'partition-size:super')
$UserdataBytes = Convert-HexSize (Get-FastbootVar 'partition-size:userdata')
if ($SuperBytes -ne [long]$Manifest.super_bytes) { throw 'Super capacity differs from this tested layout.' }
if ($UserdataBytes -ne [long]$Manifest.userdata_bytes) { throw 'Userdata capacity differs from this personalized image.' }
foreach ($Name in @('boot','init_boot','vendor_boot','vbmeta','vbmeta_system')) {
    $Capacity = Convert-HexSize (Get-FastbootVar "partition-size:${Name}_a")
    $Artifact = $Manifest.files | Where-Object { $_.path -eq "images/$Name.img" }
    if ($Capacity -lt [long]$Artifact.bytes) { throw "Partition too small: ${Name}_a" }
}
Write-Host "Read-only preflight passed for sheng $Serial. Target is slot A."
if ($Mode -eq 'Inspect') { Write-Host 'No partition was changed.'; return }
Write-Host 'Flashing will DELETE ALL USER DATA and replace the installed system.' -ForegroundColor Yellow
Write-Host 'Keep the original working package for recovery. This Pro Max build may fail to boot.'
$Confirmation = Read-Host 'Type ERASE SHENG DATA to flash this experimental package'
if ($Confirmation -cne 'ERASE SHENG DATA') { throw 'Confirmation did not match. No write was performed.' }
foreach ($Name in @('boot','init_boot','vendor_boot','vbmeta','vbmeta_system')) {
    Write-Host "Flashing ${Name}_a..."
    Write-Host (Invoke-Fastboot @('-s',$Serial,'flash',"${Name}_a",(Join-Path $PackageRoot "images\$Name.img")))
}
foreach ($Name in @('super','userdata')) {
    Write-Host "Flashing $Name (large image; please wait)..."
    Write-Host (Invoke-Fastboot @('-s',$Serial,'flash',$Name,(Join-Path $PackageRoot "images\$Name.img")))
}
# Metadata belongs to the previous Android encryption state; never touch GPT/firmware.
Write-Host (Invoke-Fastboot @('-s',$Serial,'erase','metadata'))
Write-Host (Invoke-Fastboot @('-s',$Serial,'set_active','a'))
Write-Host 'All writes succeeded; rebooting.'
Write-Host (Invoke-Fastboot @('-s',$Serial,'reboot'))
Write-Host "Flash log: $LogPath"
