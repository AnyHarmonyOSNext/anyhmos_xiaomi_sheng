# Inspect the complete incoming batch before retaining only a short boundary tail.
# A batch may contain CMD END followed by many kilobytes of kernel logs.
function Update-ProbeCommandCompletion {
    param(
        [Parameter(Mandatory=$true)][AllowEmptyString()][string]$Received,
        [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{12}$')][string]$Id,
        [Parameter(Mandatory=$true)][ref]$Tail,
        [ref]$Completion
    )
    $window=[string]$Tail.Value+$Received
    $completed=$window -match ('CMD END id='+$Id+'\b[^\r\n]*exit=(-?[0-9]+) signal=([0-9]+)\r?\n')
    if ($completed -and $null -ne $Completion) {
        $Completion.Value=[pscustomobject]@{ExitCode=[int]$Matches[1];Signal=[int]$Matches[2]}
    }
    if ($window.Length -gt 4096) { $Tail.Value=$window.Substring($window.Length-4096) }
    else { $Tail.Value=$window }
    return $completed
}
