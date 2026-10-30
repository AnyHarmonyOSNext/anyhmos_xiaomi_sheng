param(
    [ValidatePattern('^COM[0-9]+$')][string]$Port='COM21',
    [Parameter(Mandatory=$true)][string]$Script,
    [ValidateRange(2,120)][int]$Seconds=20
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Probe-Protocol.ps1')
$bytes=[System.Text.Encoding]::UTF8.GetBytes($Script)
if($bytes.Length -gt 2800){throw 'Diagnostic script exceeds the 2800-byte request limit.'}
$id=[guid]::NewGuid().ToString('N').Substring(0,12)
$request="`ncmd "+$id+' '+[Convert]::ToBase64String($bytes)+"`n"
$folder=Join-Path $PSScriptRoot 'logs'
New-Item -Path $folder -ItemType Directory -Force | Out-Null
$path=Join-Path $folder ('command-shell-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+$id+'.log')
$serial=New-Object System.IO.Ports.SerialPort $Port,115200,None,8,one
$serial.ReadBufferSize=1048576;$serial.WriteTimeout=5000
$serial.DtrEnable=$true;$serial.RtsEnable=$true;$serial.Encoding=[System.Text.Encoding]::UTF8
$writer=New-Object System.IO.StreamWriter $path,$false,([System.Text.UTF8Encoding]::new($false))
$complete=$false;$tail=''
try{
    $serial.Open();Start-Sleep -Milliseconds 500;$serial.Write($request)
    $until=(Get-Date).AddSeconds($Seconds)
    while((Get-Date) -lt $until){
        try{$text=$serial.ReadExisting()}catch{Write-Host ('Serial disconnected: '+$_.Exception.Message);break}
        if($text){$writer.Write($text);$writer.Flush()
            if(Update-ProbeCommandCompletion -Received $text -Id $id -Tail ([ref]$tail)){$complete=$true;break}}
        Start-Sleep -Milliseconds 10
    }
}finally{
    try{if($serial.IsOpen){$serial.Close()}}catch{Write-Host 'Serial closed after disconnect.'}
    try{$serial.Dispose()}finally{$writer.Dispose()}
}
[pscustomobject]@{Id=$id;Completed=$complete;Log=$path}|ConvertTo-Json -Compress
