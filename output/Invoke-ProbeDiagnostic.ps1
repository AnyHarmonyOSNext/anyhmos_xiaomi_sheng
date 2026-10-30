param([Parameter(Mandatory=$true)][string]$Script,[int]$Seconds=15,[int]$Lines=55)
$ErrorActionPreference='Stop'
$result=(& (Join-Path $PSScriptRoot 'Invoke-ProbeCommand.ps1') -Script $Script -Seconds $Seconds) | ConvertFrom-Json
$result | ConvertTo-Json -Compress
$log=Get-Content -LiteralPath $result.Log -Raw -Encoding UTF8
$start=$log.LastIndexOf('CMD BEGIN id='+$result.Id)
if($start -ge 0){$log=$log.Substring($start)}
$end=$log.IndexOf('CMD END id='+$result.Id)
if($end -ge 0){$newline=$log.IndexOf("`n",$end);if($newline -ge 0){$log=$log.Substring(0,$newline)}}
($log -split "`n" | Where-Object { $_ -notmatch '^\d+,\d+,' -and $_ -notmatch '^\[HMOS-PROBE.*(SYSCALL|NATIVE pid|PTRACED|Native service)' } | Select-Object -Last $Lines) -join "`n"
