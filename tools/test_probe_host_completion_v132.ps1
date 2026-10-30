$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../output/Probe-Protocol.ps1')
$id='2a53053fe39a'
$fixture=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../output/logs/command-shell-20261030-103608-2a53053fe39a.log') -Raw -Encoding UTF8
$pattern='CMD END id='+$id+'\b[^\r\n]*exit=[0-9]+ signal=[0-9]+\r?\n'
if ($fixture -notmatch $pattern) { throw 'Real regression fixture lacks a complete reply' }
$marker=$fixture.LastIndexOf('CMD END id='+$id)
if ($marker -lt 0 -or $fixture.Length-$marker -lt 4096) { throw 'Regression fixture no longer includes the observed trailing burst' }
$legacyTail=$fixture.Substring([Math]::Max(0,$fixture.Length-4096))
if ($legacyTail -match $pattern) { throw 'Fixture does not reproduce old truncation bug' }
$count=0
foreach ($size in @(1,7,128,512,4096,8192,32768,$fixture.Length)) {
    $tail=''; $found=$false
    for ($i=0; $i -lt $fixture.Length; $i+=$size) {
        $chunk=$fixture.Substring($i,[Math]::Min($size,$fixture.Length-$i))
        if (Update-ProbeCommandCompletion -Received $chunk -Id $id -Tail ([ref]$tail)) { $found=$true; break }
        if ($tail.Length -gt 4096) { throw 'Boundary tail grew without bound' }
    }
    if (-not $found) { throw ('Complete real reply missed at chunk size '+$size) }; $count++
}
$line=[regex]::Match($fixture,$pattern).Value
for($split=1;$split -lt $line.Length;$split++) {
    $tail=''
    if(Update-ProbeCommandCompletion -Received $line.Substring(0,$split) -Id $id -Tail ([ref]$tail)) { throw 'Partial marker accepted' }
    if(-not (Update-ProbeCommandCompletion -Received ($line.Substring($split)+('k'*16384)) -Id $id -Tail ([ref]$tail))) { throw ('Boundary marker missed at '+$split) }
    $count++
}
$tail=''
if(Update-ProbeCommandCompletion -Received $fixture -Id '000000000000' -Tail ([ref]$tail)) { throw 'Reply for another command accepted' }
$count++
foreach ($case in @(@(0,0),@(23,0),@(0,9))) {
    $tail=''; $completion=$null
    $reply='CMD END id='+$id+' pid=42 exit='+$case[0]+' signal='+$case[1]+"`n"+('k'*131072)
    if(-not (Update-ProbeCommandCompletion -Received $reply -Id $id -Tail ([ref]$tail) -Completion ([ref]$completion))) { throw 'Large batch lost upload completion' }
    if($completion.ExitCode -ne $case[0] -or $completion.Signal -ne $case[1]) { throw 'Completion result lost after tail trimming' }
    $count++
}
[pscustomobject]@{Cases=$count;RealReplyWithTrailingBurstVerified=$true;LegacyFailureReproduced=$true;NoCommandReplay=$true}|ConvertTo-Json -Compress
