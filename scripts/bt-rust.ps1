param(
    [string]$Round = "",
    [int[]]$Days,
    [string]$Strategy = "",
    [ValidateSet("all", "worse", "none")]
    [string]$TradeMatchMode = "all",
    [double]$QueuePenetration = 1.0,
    [double]$PriceSlippageBps = 0.0,
    [ValidateSet("summary", "full", "off")]
    [string]$Products = "full",
    [switch]$Carry
)

. "$PSScriptRoot\_common.ps1"

$cargoPath = Get-CargoExecutable
if (-not $cargoPath) {
    throw "Cargo is not installed, so the Rust backtester cannot run yet."
}

$roundConfig = Get-RoundConfig -Round $Round
$strategyPath = Resolve-StrategyPath -Round $roundConfig.Key -Strategy $Strategy
$dataRoots = Sync-ToolData -Round $roundConfig.Key
$dayList = @($Days | Where-Object { $null -ne $_ })
$label = if ($dayList.Count -gt 0) { $dayList -join "_" } else { "all_days" }
if ($Carry) {
    $label = "{0}_carry" -f $label
}

$runDir = New-RunDirectory -Kind "backtests" -Tool "rust" -Round $roundConfig.Key -Label $label
$summaryPath = Join-Path $runDir "run.json"
$stdoutPath = Join-Path $runDir "stdout.txt"
$outputRoot = $runDir
$datasetPath = $dataRoots.RustRoundDir

if ($dayList.Count -gt 1) {
    $datasetPath = Join-Path $runDir "dataset"
    New-Item -ItemType Directory -Force -Path $datasetPath | Out-Null
    foreach ($day in $dayList) {
        $priceFile = Join-Path $roundConfig.Root ("prices_round_{0}_day_{1}.csv" -f $roundConfig.RoundNum, $day)
        $tradeFile = Join-Path $roundConfig.Root ("trades_round_{0}_day_{1}.csv" -f $roundConfig.RoundNum, $day)
        if (-not (Test-Path $priceFile) -or -not (Test-Path $tradeFile)) {
            throw "Could not find round/day CSVs for day $day."
        }
        Copy-Item -Force -Path $priceFile -Destination (Join-Path $datasetPath ([System.IO.Path]::GetFileName($priceFile)))
        Copy-Item -Force -Path $tradeFile -Destination (Join-Path $datasetPath ([System.IO.Path]::GetFileName($tradeFile)))
    }
}

$cmd = @(
    "run", "--",
    "--trader", $strategyPath,
    "--dataset", $datasetPath,
    "--run-id", "run",
    "--output-root", $outputRoot,
    "--trade-match-mode", $TradeMatchMode,
    "--queue-penetration", $QueuePenetration,
    "--price-slippage-bps", $PriceSlippageBps,
    "--products", $Products,
    "--persist",
    "--flat"
)

if ($dayList.Count -eq 1) {
    $cmd += @("--day", [string]$dayList[0])
}
if ($Carry) {
    $cmd += "--carry"
}

$toolchainDir = Split-Path $cargoPath -Parent
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $pythonCommand) {
    $env:PYO3_PYTHON = $pythonCommand.Source
}

Push-Location (Get-ToolingConfig).Tools.paths.rustBacktesterRepo
try {
    $env:PATH = ($toolchainDir + ";" + $env:PATH)
    & $cargoPath @cmd | Tee-Object -FilePath $stdoutPath
}
finally {
    Remove-Item Env:PYO3_PYTHON -ErrorAction SilentlyContinue
    Pop-Location
}

$metricFiles = @(Get-ChildItem -Path $runDir -Recurse -Include "*metrics.json", "metrics.json" -File | Sort-Object FullName)
$submissionLogs = @(Get-ChildItem -Path $runDir -Recurse -Include "*submission.log", "submission.log" -File | Sort-Object FullName)

if ($metricFiles.Count -eq 0) {
    throw "Rust backtester did not produce any metrics.json files under $runDir"
}

$summary = [ordered]@{
    tool              = "rust"
    round             = $roundConfig.Key
    roundNumber       = $roundConfig.RoundNum
    strategyPath      = $strategyPath
    dayArgs           = $dayList
    datasetPath       = $datasetPath
    runDirectory      = $runDir
    metricFiles       = @($metricFiles | ForEach-Object { $_.FullName })
    submissionLogs    = @($submissionLogs | ForEach-Object { $_.FullName })
    tradeMatchMode    = $TradeMatchMode
    queuePenetration  = $QueuePenetration
    priceSlippageBps  = $PriceSlippageBps
    carry             = [bool]$Carry
    createdAt         = (Get-Date).ToString("o")
} | ConvertTo-Json -Depth 8

Set-Content -Path $summaryPath -Value $summary -Encoding UTF8
Write-Host ("Saved Rust run to {0}" -f $runDir)
