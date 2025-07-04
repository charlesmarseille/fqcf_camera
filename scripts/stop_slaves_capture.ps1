$targets = 1..6 | ForEach-Object { "pi$_" }
$command = 'sudo systemctl stop piSlaveTcpCamera.service'

foreach ($target in $targets) {
    ssh $target $command
}