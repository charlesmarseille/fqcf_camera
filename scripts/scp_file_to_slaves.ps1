param(
    $IPList = @("192.168.0.101", "192.168.0.102", "192.168.0.103", "192.168.0.104", "192.168.0.105", "192.168.0.106")
    [string]$FilePath,
    [string]$RemoteUser,
    [string]$RemotePath,
)

foreach ($ip in $IPList) {
    $scpCmd = "scp"
    $scpCmd += " `"$FilePath`" $RemoteUser@$ip:`"$RemotePath`""
    Write-Host "Copying to $ip..."
    Invoke-Expression $scpCmd
}