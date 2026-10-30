param([Parameter(Mandatory=$true)][string]$RecordPath)
$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
$record=Get-Content -LiteralPath $RecordPath -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($key in @('Title','DeviceState','Version','Kernel','Storage','Components','Passed','Unfinished','Next')) {
    if ($null -eq $record.$key) { throw ('Missing summary field: '+$key) }
}
$time=[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::Now,'China Standard Time').ToString('yyyy-MM-dd HH:mm:ss zzz')
function Cell([string]$Value) { return $Value.Replace('|','\|').Replace("`r",' ').Replace("`n",' ') }
$lines=[System.Collections.Generic.List[string]]::new()
$lines.Add('# 当前移植状态')
$lines.Add('')
$lines.Add('更新时间：'+$time+'。本文件由每轮完整状态记录生成。')
$lines.Add('')
$lines.Add('**'+$record.DeviceState+'**')
$lines.Add('')
$lines.Add('- 当前启动包：'+$record.Version)
$lines.Add('- 内核：'+$record.Kernel)
$lines.Add('- 存储与回退：'+$record.Storage)
if ($record.QuotaPolicy) { $lines.Add('- 额度与续接：'+$record.QuotaPolicy) }
$lines.Add('- 调试入口：[串口调试说明](output/串口调试说明.md)，双击 `output/打开调试终端.cmd`。')
$lines.Add('')
$lines.Add('| 项目 | 已验证状态／当前限制 | 证据时间 |')
$lines.Add('|---|---|---|')
foreach ($component in $record.Components) {
    $lines.Add('| '+(Cell $component.Name)+' | '+(Cell $component.State)+' | '+(Cell $component.VerifiedAt)+' |')
}
foreach ($section in @(@('本轮完成','Passed'),@('仍未完成／失败','Unfinished'),@('下一步','Next'))) {
    $lines.Add('');$lines.Add('## '+$section[0]);$lines.Add('')
    foreach ($item in $record.($section[1])) { $lines.Add('- '+$item) }
}
if ($record.Screenshot) { $lines.Add('');$lines.Add('截图：'+$record.Screenshot) }
if ($record.Evidence) {
    $lines.Add('');$lines.Add('## 本轮证据');$lines.Add('')
    foreach ($item in $record.Evidence) { $lines.Add('- `'+$item+'`') }
}
$lines.Add('');$lines.Add('详细历史：[续接进展](analysis/20261027续接进展.md)。以后每轮结束都更新本文件，并追加到 [轮次总结](analysis/轮次总结.md)。')
$body=$lines -join "`r`n"
$encoding=[Text.UTF8Encoding]::new($false)
$current=Join-Path $workspace '当前状态.md'
[IO.File]::WriteAllText($current,$body+"`r`n",$encoding)
$history=Join-Path $workspace 'analysis\轮次总结.md'
if (-not (Test-Path -LiteralPath $history)) { [IO.File]::WriteAllText($history,"# 移植轮次总结`r`n`r`n每轮保留完整状态、未完成项和下一步；主入口为工作区的当前状态.md。`r`n",$encoding) }
$historyBody=($body -replace '^# 当前移植状态','### 完整状态快照').Replace('(output/','(../output/').Replace('(analysis/','(')
[IO.File]::AppendAllText($history,"`r`n---`r`n`r`n## "+$time+' '+$record.Title+"`r`n`r`n"+$historyBody+"`r`n",$encoding)
Write-Output $current
