param(
    [switch]$OpenLatestFolder
)

. "$PSScriptRoot\_common.ps1"

Ensure-GsgillVisualizerDependencies

$config = Get-ToolingConfig
$repo = $config.Tools.paths.gsgillVisualizerRepo
$port = [int]$config.Tools.ports.gsgillVisualizer
$url = "http://127.0.0.1:{0}/" -f $port

Start-Process -WindowStyle Minimized -FilePath "python" -ArgumentList "-m", "http.server", "$port" -WorkingDirectory $repo | Out-Null

$latest = $null
try {
    $latest = Get-LatestRunInfo
}
catch {
}

Write-Host ("gsgill visualizer started at {0}" -f $url)
if ($null -ne $latest) {
    Write-Host ("Latest run log: {0}" -f $latest.logPath)
    if ($OpenLatestFolder) {
        Start-Process explorer.exe "/select,$($latest.logPath)" | Out-Null
    }
}
