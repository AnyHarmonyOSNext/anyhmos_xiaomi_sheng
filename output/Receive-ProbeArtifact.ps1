param(
 [Parameter(Mandatory=$true)][ValidatePattern('^/hmos-root/data/local/tmp/[A-Za-z0-9_./-]+$')][string]$Source,
 [Parameter(Mandatory=$true)][string]$Destination,
 [ValidatePattern('^COM[0-9]+$')][string]$Port='COM21',
 [ValidateRange(1,24)][int]$ChunksPerRequest=24
)
$ErrorActionPreference='Stop'
if($Source -match '/\.\.?(/|$)'){throw 'Invalid source path'}
$absolute=[IO.Path]::GetFullPath($Destination)
if(Test-Path -LiteralPath $absolute){throw 'Destination already exists'}
$nonce=[guid]::NewGuid().ToString('N').Substring(0,12)
$chunkSize=600
function Read-Reply([string]$Script){
 $r=(& (Join-Path $PSScriptRoot 'Invoke-ProbeCommand.ps1') -Port $Port -Script $Script -Seconds 30)|ConvertFrom-Json
 $log=Get-Content -LiteralPath $r.Log -Raw -Encoding UTF8
 if(-not $r.Completed -or $log -notmatch ('CMD END id='+$r.Id+'\b[^\r\n]*exit=0 signal=0')){throw ('Read failed; inspect '+$r.Log)}
 return $log
}
$meta=Read-Reply ('set -e; printf "META '+$nonce+' %s %s\n" "$(stat -c %s '+$Source+')" "$(sha256sum '+$Source+' | cut -d " " -f1)"')
$m=[regex]::Match($meta,('META '+$nonce+' ([0-9]+) ([a-f0-9]{64})'))
if(-not $m.Success){throw 'Missing metadata'}
$length=[int]$m.Groups[1].Value;$expected=$m.Groups[2].Value
if($length -lt 1 -or $length -gt 1048576){throw 'Artifact must be 1 byte to 1 MiB'}
$memory=[IO.MemoryStream]::new()
try{
 $count=[int][Math]::Ceiling($length/[double]$chunkSize)
 for($start=0;$start -lt $count;$start+=$ChunksPerRequest){
  $end=[Math]::Min($start+$ChunksPerRequest,$count)
  $reply=Read-Reply ('set -e; i='+$start+'; while [ "$i" -lt '+$end+' ]; do data=$(dd if='+$Source+' bs='+$chunkSize+' skip="$i" count=1 2>/dev/null | base64 -w0); printf "CHUNK '+$nonce+' %s %s\n" "$i" "$data"; i=$((i+1)); done')
  for($i=$start;$i -lt $end;$i++){
   $expectedChunkLength=[Math]::Min($chunkSize,$length-$i*$chunkSize)
   $candidate=$reply
   $raw=$null
   for($attempt=0;$attempt -lt 4;$attempt++) {
    $chunk=[regex]::Match($candidate,('(?m)^CHUNK '+$nonce+' '+$i+' ([A-Za-z0-9+/=]+)\r?$'))
    if($chunk.Success) {
     try { $decoded=[Convert]::FromBase64String($chunk.Groups[1].Value); if($decoded.Length -eq $expectedChunkLength){$raw=$decoded;break} } catch [FormatException] { }
    }
    if($attempt -lt 3) {
     $candidate=Read-Reply ('set -e; data=$(dd if='+$Source+' bs='+$chunkSize+' skip='+$i+' count=1 2>/dev/null | base64 -w0); printf "CHUNK '+$nonce+' '+$i+' %s\n" "$data"')
    }
   }
   if($null -eq $raw){throw ('Missing or corrupt chunk after retries: '+$i)}
   $memory.Write($raw,0,$raw.Length)
  }
 }
 $bytes=$memory.ToArray()
}finally{$memory.Dispose()}
$hasher=[Security.Cryptography.SHA256]::Create()
try{$actual=([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
if($bytes.Length -ne $length -or $actual -ne $expected){throw 'Artifact integrity mismatch'}
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($absolute))|Out-Null
[IO.File]::WriteAllBytes($absolute,$bytes)
[pscustomobject]@{Source=$Source;Destination=$absolute;Bytes=$length;Sha256=$actual;Verified=$true}|ConvertTo-Json -Compress
