param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][ValidatePattern('^/hmos-root/data/local/tmp/[A-Za-z0-9_./-]+$')][string]$Destination,
    [ValidatePattern('^COM[0-9]+$')][string]$Port='COM21'
)
$ErrorActionPreference='Stop'
if ($Destination -match '/\.\.?(/|$)' -or $Destination.EndsWith('/')) { throw 'Invalid RAM destination' }
$bytes=[System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Path).Path)
if ($bytes.Length -gt 1048576) { throw 'Diagnostic upload is limited to 1 MiB' }
$sha=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
$temporary=$Destination+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
function Send-Script([string]$Script) {
    $raw=& (Join-Path $PSScriptRoot 'Invoke-ProbeCommand.ps1') -Port $Port -Script $Script -Seconds 12
    $result=$raw | ConvertFrom-Json
    if (-not $result.Completed) { throw ('Upload command did not finish; see '+$result.Log) }
    $log=Get-Content -LiteralPath $result.Log -Raw
    if ($log -notmatch ('CMD END id='+$result.Id+'\b[^\r\n]*exit=0 signal=0')) { throw ('Upload command failed; see '+$result.Log) }
}
Send-Script ('set -e; : > '+$temporary)
for ($offset=0;$offset -lt $bytes.Length;$offset+=1800) {
    $length=[Math]::Min(1800,$bytes.Length-$offset)
    $chunk=[Convert]::ToBase64String($bytes,$offset,$length)
    Send-Script ('set -e; printf %s '+$chunk+' | base64 -d >> '+$temporary)
}
Send-Script ('set -e; actual=$(sha256sum '+$temporary+' | cut -d " " -f1); test "$actual" = '+$sha+'; chmod 0755 '+$temporary+'; mv '+$temporary+' '+$Destination)
[pscustomobject]@{Destination=$Destination;Bytes=$bytes.Length;Sha256=$sha;Verified=$true} | ConvertTo-Json -Compress
