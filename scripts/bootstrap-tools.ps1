param(
    [switch]$SkipVisualizers,
    [switch]$SkipMonteCarlo
)

. "$PSScriptRoot\_common.ps1"

Write-Host "Bootstrapping replay backtesters..."
Ensure-XeeshanEnvironment
Ensure-KevinEnvironment

Write-Host "Syncing local round data mirrors..."
Sync-ToolData -Round tutorial | Out-Null
Sync-ToolData -Round round1 | Out-Null

if (-not $SkipVisualizers) {
    Write-Host "Installing visualizer dependencies..."
    Ensure-GsgillVisualizerDependencies
    Ensure-KevinVisualizerDependencies
}

if (-not $SkipMonteCarlo) {
    Write-Host "Bootstrapping Monte Carlo environment..."
    Ensure-ChrisEnvironment

    if (-not (Get-CargoExecutable)) {
        Write-Warning "Rust/Cargo is not installed. Chris's Monte Carlo tool is configured, but live Monte Carlo runs will fail until cargo is available."
    }
}

Write-Host "Bootstrap complete."
