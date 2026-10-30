param([Parameter(Mandatory=$true)][int]$WindowId,[Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Prefix)
$ErrorActionPreference='Stop'
function Confirm-GuidePage([string]$Key,[string]$Needle) {
    for($attempt=0;$attempt -lt 5;$attempt++) {
        $file='/data/local/tmp/'+$Prefix+'-'+$Key+'-'+$attempt+'.txt'
        $script='B=/busybox; R=/hmos-root; $B chroot $R /data/local/tmp/native_sa_dump 4606 '+$file+' -w '+$WindowId+' -inspector; $B sleep 1; if $B grep -q "'+$Needle+'" "$R'+$file+'"; then echo GUIDE_EXPECTED_PAGE=1; else echo GUIDE_EXPECTED_PAGE=0; fi; $B grep -E "text:|accessibilityText:" "$R'+$file+'" | $B grep -v -E "text: $|Text: $" | $B tail -n 5'
        $reply=(& (Join-Path $PSScriptRoot 'Invoke-ProbeDiagnostic.ps1') -Script $script -Seconds 7 -Lines 15 | Out-String)
        Write-Output $reply
        if($reply -match 'GUIDE_EXPECTED_PAGE=1'){return}
        Start-Sleep -Seconds 1
    }
    throw ('Expected guide page unavailable: '+$Key)
}
function Click-Guide([string]$Arguments) {
    & (Join-Path $PSScriptRoot 'Invoke-NativeInput.ps1') -Arguments $Arguments
}
Confirm-GuidePage 'welcome' 'accessibilityText: 欢迎'
Click-Guide '-T -c 1524 1813'
Confirm-GuidePage 'language' 'text: 简体中文'
Click-Guide '-T -c 1524 1828'
Confirm-GuidePage 'region' 'text: 中国'
Click-Guide '-T -c 1524 1828'
Confirm-GuidePage 'quick' 'text: 跳过'
Click-Guide '-T -c 1524 1949'
Confirm-GuidePage 'agreement' 'text: 同意并继续'
Click-Guide '-T -m 1500 1550 1500 650 650'
Click-Guide '-T -c 1524 1828'
Write-Output 'Known guide pages completed; inspect the privacy extension before continuing.'
