param()

. "$PSScriptRoot\_common.ps1"

Ensure-KevinVisualizerDependencies

$config = Get-ToolingConfig
$repo = $config.Tools.paths.kevinVisualizerRepo
$port = [int]$config.Tools.ports.kevinVisualizer
$url = "http://127.0.0.1:{0}/" -f $port

Start-Process -WindowStyle Minimized -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev -- --host 127.0.0.1 --port $port" -WorkingDirectory $repo | Out-Null

$latest = $null
try {
    $latest = Get-LatestRunInfo
}
catch {
}

Write-Host ("Kevin visualizer started at {0}" -f $url)
if ($null -ne $latest) {
    Write-Host ("Latest run log: {0}" -f $latest.logPath)
}
