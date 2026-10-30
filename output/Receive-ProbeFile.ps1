param(
    [Parameter(Mandatory=$true)][ValidatePattern('^/hmos-root/data/local/tmp/[A-Za-z0-9_./-]+$')][string]$Source,
    [Parameter(Mandatory=$true)][string]$Destination,
    [ValidatePattern('^COM[0-9]+$')][string]$Port='COM21'
)
$ErrorActionPreference='Stop'
if ($Source -match '/\.\.?(/|$)') { throw 'Invalid RAM source path' }
$nonce=[guid]::NewGuid().ToString('N').Substring(0,12)
function Read-Reply([string]$Script) {
    $result=(& (Join-Path $PSScriptRoot 'Invoke-ProbeCommand.ps1') -Port $Port -Script $Script -Seconds 12) | ConvertFrom-Json
    if (-not $result.Completed) { throw ('Read command timed out; see '+$result.Log) }
    $log=Get-Content -LiteralPath $result.Log -Raw -Encoding UTF8
    if ($log -notmatch ('CMD END id='+$result.Id+'\b[^\r\n]*exit=0 signal=0')) { throw ('Read failed; see '+$result.Log) }
    return $log
}
$metadata=Read-Reply ('set -e; printf "PROBE_META '+$nonce+' %s %s\n" "$(stat -c %s '+$Source+')" "$(sha256sum '+$Source+' | cut -d " " -f1)"')
$match=[regex]::Match($metadata,('PROBE_META '+$nonce+' ([0-9]+) ([a-f0-9]{64})'))
if (-not $match.Success) { throw 'No valid source metadata' }
$length=[int]$match.Groups[1].Value;$expected=$match.Groups[2].Value
if ($length -lt 1 -or $length -gt 1048576) { throw 'Diagnostic receive is limited to 1 MiB' }
$memory=[System.IO.MemoryStream]::new()
try {
    for ($i=0;$i -lt [Math]::Ceiling($length/1800.0);$i++) {
        $chunkMatch=$null
        for ($attempt=0;$attempt -lt 3;$attempt++) {
            $script='set -e; data=$(dd if='+$Source+' bs=1800 skip='+$i+' count=1 2>/dev/null | base64 -w0); printf "PROBE_CHUNK '+$nonce+' '+$i+' %s\n" "$data"'
            $reply=Read-Reply $script
            $chunkMatch=[regex]::Match($reply,('(?m)^PROBE_CHUNK '+$nonce+' '+$i+' ([A-Za-z0-9+/=]+)\r?$'))
            if ($chunkMatch.Success) { break }
        }
        if (-not $chunkMatch.Success) { throw ('No intact chunk '+$i) }
        $raw=[Convert]::FromBase64String($chunkMatch.Groups[1].Value)
        if ($raw.Length -ne [Math]::Min(1800,$length-$i*1800)) { throw ('Wrong chunk length '+$i) }
        $memory.Write($raw,0,$raw.Length)
    }
    $bytes=$memory.ToArray()
} finally { $memory.Dispose() }
$hasher=[Security.Cryptography.SHA256]::Create()
try { $actual=([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $hasher.Dispose() }
if ($bytes.Length -ne $length -or $actual -ne $expected) { throw 'Received file integrity check failed' }
$absolute=[IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $absolute) { throw 'Destination already exists; choose a new artifact name' }
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($absolute)) | Out-Null
[IO.File]::WriteAllBytes($absolute,$bytes)
[pscustomobject]@{Source=$Source;Destination=$absolute;Bytes=$length;Sha256=$actual;Verified=$true}|ConvertTo-Json -Compress
