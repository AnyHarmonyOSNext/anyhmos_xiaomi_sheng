param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][ValidatePattern('^/hmos-root/data/local/tmp/[A-Za-z0-9_./-]+$')][string]$Destination,
    [ValidatePattern('^COM[0-9]+$')][string]$Port='COM21'
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Probe-Protocol.ps1')
if ($Destination -match '/\.\.?(/|$)' -or $Destination.EndsWith('/')) { throw 'Invalid destination' }
$bytes=[IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Path).Path)
if ($bytes.Length -gt 1048576) { throw 'Upload is limited to 1 MiB' }
$sha=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
$temporary=$Destination+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
$log=Join-Path $PSScriptRoot ('logs/upload-stream-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)+'.log')
$writer=[IO.StreamWriter]::new($log,$false,[Text.UTF8Encoding]::new($false))
$serial=[IO.Ports.SerialPort]::new($Port,115200,[IO.Ports.Parity]::None,8,[IO.Ports.StopBits]::One)
$serial.ReadBufferSize=1048576; $serial.WriteTimeout=5000
$serial.DtrEnable=$true; $serial.RtsEnable=$true; $serial.Encoding=[Text.Encoding]::UTF8
function Invoke-UploadCommand([string]$script) {
    $id=[guid]::NewGuid().ToString('N').Substring(0,12)
    $request="`ncmd "+$id+' '+[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($script))+"`n"
    $serial.Write($request)
    $until=(Get-Date).AddSeconds(60); $tail=''; $completion=$null
    while ((Get-Date) -lt $until) {
        $chunk=$serial.ReadExisting()
        if ($chunk) {
            $writer.Write($chunk); $writer.Flush()
            if (Update-ProbeCommandCompletion -Received $chunk -Id $id -Tail ([ref]$tail) -Completion ([ref]$completion)) {
                if ($completion.ExitCode -ne 0 -or $completion.Signal -ne 0) { throw "Upload command failed, see $log" }
                return
            }
        }
        Start-Sleep -Milliseconds 10
    }
    throw "Upload command $id timed out; inspect $log before retrying"
}
try {
    $serial.Open(); Start-Sleep -Milliseconds 500
    Invoke-UploadCommand ('set -e; : > '+$temporary)
    for ($offset=0;$offset -lt $bytes.Length;$offset+=1800) {
        $length=[Math]::Min(1800,$bytes.Length-$offset)
        $chunk=[Convert]::ToBase64String($bytes,$offset,$length)
        Invoke-UploadCommand ('set -e; printf %s '+$chunk+' | base64 -d >> '+$temporary)
    }
    Invoke-UploadCommand ('set -e; actual=$(sha256sum '+$temporary+' | cut -d " " -f1); test "$actual" = '+$sha+'; chmod 0755 '+$temporary+'; mv '+$temporary+' '+$Destination)
} finally {
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose(); $writer.Dispose()
}
[pscustomobject]@{Destination=$Destination;Bytes=$bytes.Length;Sha256=$sha;Verified=$true;Log=$log} | ConvertTo-Json -Compress
