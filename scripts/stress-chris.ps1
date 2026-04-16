param(
    [string]$Round = "tutorial",
    [string]$Strategy = "",
    [ValidateSet("default", "quick", "heavy")]
    [string]$Preset = "quick",
    [switch]$Visualize
)

. "$PSScriptRoot\_common.ps1"

$roundConfig = Get-RoundConfig -Round $Round
if ($roundConfig.Key -ne "tutorial") {
    throw "Chris's Monte Carlo simulator currently supports the tutorial round only. Use -Round tutorial."
}

$cargoPath = Get-CargoExecutable
if (-not $cargoPath) {
    throw "Cargo is not installed, so Chris's Monte Carlo simulator cannot run yet."
}

Ensure-ChrisEnvironment

$strategyPath = Resolve-StrategyPath -Round $roundConfig.Key -Strategy $Strategy
$runDir = New-RunDirectory -Kind "stress" -Tool "chris" -Round $roundConfig.Key -Label $Preset
$dashboardPath = Join-Path $runDir "dashboard.json"
$pythonPath = Get-VenvPython -VenvDir (Get-ToolingConfig).Tools.envs.chrisVenv

$cmd = @("-m", "prosperity4mcbt", $strategyPath, "--out", $dashboardPath)
switch ($Preset) {
    "quick" { $cmd += "--quick" }
    "heavy" { $cmd += "--heavy" }
}
if ($Visualize) {
    $cmd += "--vis"
}

Push-Location (Join-Path (Get-ToolingConfig).Tools.paths.chrisMonteCarloRepo "backtester")
try {
    $env:PATH = ((Split-Path $cargoPath -Parent) + ";" + $env:PATH)
    & $pythonPath @cmd | Tee-Object -FilePath (Join-Path $runDir "stdout.txt")
}
finally {
    Pop-Location
}

$summary = [ordered]@{
    tool          = "chris"
    round         = $roundConfig.Key
    strategyPath  = $strategyPath
    dashboardPath = $dashboardPath
    preset        = $Preset
    runDirectory  = $runDir
    createdAt     = (Get-Date).ToString("o")
} | ConvertTo-Json -Depth 6

Set-Content -Path (Join-Path $runDir "run.json") -Value $summary -Encoding UTF8
Write-Host ("Saved Chris Monte Carlo run to {0}" -f $runDir)
