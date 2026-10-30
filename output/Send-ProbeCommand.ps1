param(
    [Parameter(Mandatory=$true)][ValidatePattern('^COM[0-9]+$')][string]$Port,
    [Parameter(Mandatory=$true)][ValidateSet('status','diag','ipc','ipc0','ipc1','ipc2','ipc3','test-token','test-binder','replay','trace','hmos-list','hmos','reboot-recovery')][string]$Command,
    [ValidateRange(2,120)][int]$Seconds=15
)
$ErrorActionPreference = 'Stop'
$folder = Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Path $folder -Force | Out-Null
$path = Join-Path $folder ('command-' + $Command + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
$portObject = New-Object System.IO.Ports.SerialPort $Port,115200,None,8,one
$portObject.DtrEnable = $true
$portObject.RtsEnable = $true
$portObject.Encoding = [System.Text.Encoding]::UTF8
$writer = New-Object System.IO.StreamWriter $path,$false,([System.Text.UTF8Encoding]::new($false))
try {
    $portObject.Open()
    Start-Sleep -Milliseconds 500
    $portObject.Write($Command + "`n")
    $end = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $end) {
        try { $s = $portObject.ReadExisting() } catch { Write-Host ('Serial disconnected: ' + $_.Exception.Message); break }
        if ($s) { $writer.Write($s); $writer.Flush() }
        Start-Sleep -Milliseconds 10
    }
} finally {
    try { if ($portObject.IsOpen) { $portObject.Close() } } catch { Write-Host ('Serial close after disconnect: ' + $_.Exception.Message) }
    try { $portObject.Dispose() } finally { $writer.Dispose() }
}
Write-Host "Saved: $path"
