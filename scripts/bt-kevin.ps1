param(
    [string]$Round = "",
    [int[]]$Days,
    [string]$Strategy = "",
    [ValidateSet("all", "worse", "none")]
    [string]$MatchTrades = "worse",
    [switch]$PrintTraderOutput
)

. "$PSScriptRoot\_common.ps1"

$roundConfig = Get-RoundConfig -Round $Round
$strategyPath = Resolve-StrategyPath -Round $roundConfig.Key -Strategy $Strategy
$dataRoots = Sync-ToolData -Round $roundConfig.Key

Ensure-KevinEnvironment

$dayList = @($Days)
$dayArgs = Convert-DayArgs -RoundConfig $roundConfig -Days $Days
$label = if ($dayList.Count -gt 0) { $dayList -join "_" } else { "all_days" }
$runDir = New-RunDirectory -Kind "backtests" -Tool "kevin" -Round $roundConfig.Key -Label $label
$outPath = Join-Path $runDir "kevin.log"
$summaryPath = Join-Path $runDir "run.json"
$pythonPath = Get-VenvPython -VenvDir (Get-ToolingConfig).Tools.envs.kevinVenv
$env:PYTHONPATH = (Get-ToolingConfig).Tools.paths.kevinBacktesterRepo

$cmd = @(
    "-m", "prosperity4bt",
    $strategyPath
) + $dayArgs + @(
    "--out", $outPath,
    "--data", $dataRoots.KevinRoot,
    "--match-trades", $MatchTrades,
    "--no-vis"
)

if (-not $PrintTraderOutput) {
    $cmd += "--no-progress"
}
else {
    $cmd += "--print"
}

Push-Location (Get-ToolingConfig).Tools.paths.kevinBacktesterRepo
try {
    & $pythonPath @cmd | Tee-Object -FilePath (Join-Path $runDir "stdout.txt")
}
finally {
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    Pop-Location
}

if (-not (Test-Path $outPath)) {
    throw "Kevin backtester did not produce an output log at $outPath"
}

$summary = [ordered]@{
    tool         = "kevin"
    round        = $roundConfig.Key
    roundNumber  = $roundConfig.RoundNum
    strategyPath = $strategyPath
    dayArgs      = $dayArgs
    outPath      = $outPath
    dataRoot     = $dataRoots.KevinRoot
    runDirectory = $runDir
    createdAt    = (Get-Date).ToString("o")
} | ConvertTo-Json -Depth 6

Set-Content -Path $summaryPath -Value $summary -Encoding UTF8
Write-LatestRunPointers -Tool "kevin" -Round $roundConfig.Key -RunDir $runDir -LogPath $outPath -StrategyPath $strategyPath

Write-Host ("Saved Kevin run to {0}" -f $runDir)
