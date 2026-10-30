param([Parameter(Mandatory=$true)][ValidatePattern('^COM[0-9]+$')][string]$Port, [ValidateRange(10,600)][int]$Seconds=60)
$ErrorActionPreference = 'Stop'
$folder = Join-Path $PSScriptRoot 'logs'
New-Item -ItemType Directory -Path $folder -Force | Out-Null
$path = Join-Path $folder ('usb-' + $Port + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
$serial = New-Object System.IO.Ports.SerialPort $Port,115200,None,8,one
$serial.DtrEnable = $true
$serial.RtsEnable = $true
$serial.Encoding = [System.Text.Encoding]::UTF8
$writer = New-Object System.IO.StreamWriter $path,$false,([System.Text.UTF8Encoding]::new($false))
try {
    $serial.Open()
    Start-Sleep -Milliseconds 500
    $serial.Write("replay`n")
    $end = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $end) {
        $s = $serial.ReadExisting()
        if ($s) { $writer.Write($s); $writer.Flush(); Write-Host -NoNewline $s }
        Start-Sleep -Milliseconds 50
    }
} finally {
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose()
    $writer.Dispose()
}
Write-Host "`nSaved: $path"
