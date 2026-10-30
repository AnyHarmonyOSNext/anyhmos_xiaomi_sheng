param([string]$Serial='YOUR_DEVICE_SERIAL',[ValidatePattern('^v[1-9][0-9]*$')][string]$Version)
. (Join-Path $PSScriptRoot 'Common.ps1')
Require-Success (Invoke-DeviceTool $Adb @('-s',$Serial,'shell','test -d /tmp/hmos-data-read/local/tmp'))
$files=Invoke-DeviceTool $Adb @('-s',$Serial,'shell',('ls /tmp/hmos-data-read/local/tmp/'+$Version+'*.txt'))
if($files.Code -ne 0){throw $files.Text}
$names=@($files.Text -split "`n" | ForEach-Object {Split-Path $_.Trim() -Leaf})
if(-not $names.Count -or ($names | Where-Object {$_ -notmatch ('^'+$Version+'[A-Za-z0-9_-]*\.txt$')})){throw 'Invalid diagnostic filenames'}
$dest=Join-Path $PSScriptRoot ('logs/'+$Version+'-persistent-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.tar')
$info=[Diagnostics.ProcessStartInfo]::new()
$info.FileName=$Adb
foreach($arg in @('-s',$Serial,'exec-out','tar','-cf','-','-C','/tmp/hmos-data-read/local/tmp')+$names){$info.ArgumentList.Add($arg)}
$info.UseShellExecute=$false;$info.CreateNoWindow=$true
$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
$proc=[Diagnostics.Process]::Start($info)
$stream=[IO.File]::Create($dest)
try{$proc.StandardOutput.BaseStream.CopyTo($stream)}finally{$stream.Dispose()}
$err=$proc.StandardError.ReadToEnd();$proc.WaitForExit();$code=$proc.ExitCode;$proc.Dispose()
if($code -ne 0){throw $err}
[pscustomobject]@{Path=$dest;Files=$names.Count;Bytes=(Get-Item -LiteralPath $dest).Length;Sha256=(Get-FileHash -LiteralPath $dest).Hash}|ConvertTo-Json -Compress
