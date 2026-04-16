param(
    [string]$Round = "",
    [int[]]$Days,
    [string]$Strategy = "",
    [ValidateSet("all", "worse", "none")]
    [string]$MatchTrades = "all",
    [switch]$PrintTraderOutput
)

. "$PSScriptRoot\_common.ps1"

$roundConfig = Get-RoundConfig -Round $Round
$strategyPath = Resolve-StrategyPath -Round $roundConfig.Key -Strategy $Strategy
$dataRoots = Sync-ToolData -Round $roundConfig.Key

Ensure-XeeshanEnvironment

$dayArgs = Convert-DayArgs -RoundConfig $roundConfig -Days $Days
$label = if ($Days.Count -gt 0) { $Days -join "_" } else { "all_days" }
$runDir = New-RunDirectory -Kind "backtests" -Tool "xeeshan" -Round $roundConfig.Key -Label $label
$outPath = Join-Path $runDir "xeeshan.log"
$summaryPath = Join-Path $runDir "run.json"
$pythonPath = Get-VenvPython -VenvDir (Get-ToolingConfig).Tools.envs.xeeshanVenv

$cmd = @(
    "-m", "prosperity4bt",
    $strategyPath
) + $dayArgs + @(
    "--out", $outPath,
    "--data", $dataRoots.XeeshanRoot,
    "--match-trades", $MatchTrades,
    "--merge-pnl"
)

if ($PrintTraderOutput) {
    $cmd += "--print"
}
else {
    $cmd += "--no-progress"
}

Push-Location (Get-ToolingConfig).Tools.paths.xeeshanBacktesterRepo
try {
    & $pythonPath @cmd | Tee-Object -FilePath (Join-Path $runDir "stdout.txt")
}
finally {
    Pop-Location
}

if (-not (Test-Path $outPath)) {
    throw "Xeeshan backtester did not produce an output log at $outPath"
}

$summary = [ordered]@{
    tool         = "xeeshan"
    round        = $roundConfig.Key
    roundNumber  = $roundConfig.RoundNum
    strategyPath = $strategyPath
    dayArgs      = $dayArgs
    outPath      = $outPath
    dataRoot     = $dataRoots.XeeshanRoot
    runDirectory = $runDir
    createdAt    = (Get-Date).ToString("o")
} | ConvertTo-Json -Depth 6

Set-Content -Path $summaryPath -Value $summary -Encoding UTF8
Write-LatestRunPointers -Tool "xeeshan" -Round $roundConfig.Key -RunDir $runDir -LogPath $outPath -StrategyPath $strategyPath

Write-Host ("Saved Xeeshan run to {0}" -f $runDir)
