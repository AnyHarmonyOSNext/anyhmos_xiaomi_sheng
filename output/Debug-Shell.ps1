param(
    [ValidatePattern('^COM[0-9]+$')][string]$Port='COM21',
    [ValidateSet('Hmos','Probe')][string]$Target='Hmos',
    [string]$Command,
    [ValidateRange(3,120)][int]$Seconds=65
)
$ErrorActionPreference='Stop'
function ConvertTo-ShellLiteral([string]$Value) {
    $q="'"
    $replacement=$q+'"'+$q+'"'+$q
    return $q+$Value.Replace($q,$replacement)+$q
}
function Show-Help {
    Write-Host @'
输入 Linux 命令后回车。默认在鸿蒙根中执行。
  :hmos    切到鸿蒙 /system/bin/sh
  :probe   切到诊断 BusyBox（鸿蒙根位于 /hmos-root）
  :ports   显示电脑串口
  :help    显示帮助
  :exit    退出
例：ps -A
    hilog -x -T SAMGR
    param get bootevent.composer_host.ready
每行是独立命令；cd 请和后续命令写在同一行。不提供远端交互 TTY。
'@
}
function Invoke-Line([string]$Text,[string]$Scope) {
    $script=$Text
    if ($Scope -eq 'Hmos') { $script='chroot /hmos-root /system/bin/sh -c '+(ConvertTo-ShellLiteral $Text) }
    $reply=& (Join-Path $PSScriptRoot 'Invoke-ProbeCommand.ps1') -Port $Port -Script $script -Seconds $Seconds
    $result=$reply | ConvertFrom-Json
    $raw=Get-Content -LiteralPath $result.Log -Raw
    if (-not $raw) { $raw='' }
    $begin=$raw.IndexOf('CMD BEGIN id='+$result.Id)
    $finish=[regex]::Match($raw,'(?m)^\[HMOS-PROBE[^\r\n]*\] CMD END id='+$result.Id+'\b[^\r\n]*exit=(-?\d+) signal=(\d+)')
    if ($begin -ge 0) {
        $start=$raw.IndexOf("`n",$begin)+1
        $end=if ($finish.Success) { $finish.Index } else { $raw.Length }
        if ($end -gt $start) { Write-Host $raw.Substring($start,$end-$start).TrimEnd() }
    } elseif ($raw.Length) {
        Write-Warning '开始标记未完整收到；显示串口日志末尾，完整内容已保留。'
        Write-Host (($raw -split "`r?`n" | Select-Object -Last 70) -join "`n")
    }
    if ($result.Completed -and $finish.Success) {
        Write-Host ('[exit='+$finish.Groups[1].Value+' signal='+$finish.Groups[2].Value+'] '+$result.Log)
    } else {
        Write-Warning ('未收到本条命令的结束回包；端口枚举不代表调试通道正常。日志：'+$result.Log)
    }
}
if ($PSBoundParameters.ContainsKey('Command')) { Invoke-Line $Command $Target; return }
Write-Host ('sheng USB 调试命令终端 / '+$Port)
Show-Help
while ($true) {
    $line=Read-Host ($Target.ToUpperInvariant()+'('+$Port+')')
    if ($null -eq $line) { break }
    $line=$line.Trim()
    if (-not $line) { continue }
    switch ($line.ToLowerInvariant()) {
        ':exit' { return }
        ':help' { Show-Help; continue }
        ':hmos' { $Target='Hmos'; continue }
        ':probe' { $Target='Probe'; continue }
        ':ports' { [System.IO.Ports.SerialPort]::GetPortNames() | ForEach-Object { Write-Host $_ }; continue }
        default { try { Invoke-Line $line $Target } catch { Write-Warning $_.Exception.Message } }
    }
}
