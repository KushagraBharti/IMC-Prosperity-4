param(
    [Parameter(Mandatory = $true)]
    [string[]]$Strategy,
    [string]$WindowDir = "",
    [ValidateSet("kevin", "xeeshan", "both")]
    [string]$Tool = "both",
    [ValidateSet("all", "worse", "none")]
    [string]$KevinMatchTrades = "worse",
    [ValidateSet("all", "worse", "none")]
    [string]$XeeshanMatchTrades = "all",
    [string]$Label = ""
)

. "$PSScriptRoot\_common.ps1"

$config = Get-ToolingConfig
$roundConfig = Get-RoundConfig -Round "round3"
$projectRoot = $config.ProjectRoot

if ([string]::IsNullOrWhiteSpace($WindowDir)) {
    $WindowDir = Join-Path $projectRoot "outputs\official-windows\round3_day2_0_99900_from_442527"
}

if (-not (Test-Path $WindowDir)) {
    throw "Portal window directory does not exist: $WindowDir"
}

$prices = Join-Path $WindowDir "prices_round_3_day_2.csv"
$trades = Join-Path $WindowDir "trades_round_3_day_2.csv"
if (-not (Test-Path $prices)) {
    throw "Portal window prices file missing: $prices"
}
if (-not (Test-Path $trades)) {
    throw "Portal window trades file missing: $trades"
}

$safeLabel = if ([string]::IsNullOrWhiteSpace($Label)) { "round3_portal_window" } else { $Label }
$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$batchDir = Join-Path (Get-OutputRoot) ("batch-backtests\{0}_{1}" -f $safeLabel, $stamp)
New-Item -ItemType Directory -Force -Path $batchDir | Out-Null

$dataRoot = Join-Path $batchDir "data"
$dataRound = Join-Path $dataRoot "round3"
New-Item -ItemType Directory -Force -Path $dataRound | Out-Null
Copy-Item -Force -LiteralPath $prices -Destination (Join-Path $dataRound "prices_round_3_day_2.csv")
Copy-Item -Force -LiteralPath $trades -Destination (Join-Path $dataRound "trades_round_3_day_2.csv")

$tools = if ($Tool -eq "both") { @("kevin", "xeeshan") } else { @($Tool) }
$rows = @()

function Get-RunTotal {
    param([string]$Text)

    $matches = [regex]::Matches($Text, "Total profit:\s*([-0-9,.]+)")
    if ($matches.Count -eq 0) {
        return ""
    }
    return $matches[$matches.Count - 1].Groups[1].Value.Replace(",", "")
}

foreach ($strategyInput in $Strategy) {
    $strategyPath = Resolve-Path $strategyInput
    $strategyName = Split-Path $strategyPath -Leaf

    foreach ($toolName in $tools) {
        $runDir = Join-Path $batchDir ("{0}_{1}" -f ([IO.Path]::GetFileNameWithoutExtension($strategyName)), $toolName)
        New-Item -ItemType Directory -Force -Path $runDir | Out-Null
        $outPath = Join-Path $runDir "$toolName.log"
        $stdoutPath = Join-Path $runDir "stdout.txt"

        if ($toolName -eq "kevin") {
            Ensure-KevinEnvironment
            $pythonPath = Get-VenvPython -VenvDir $config.Tools.envs.kevinVenv
            $env:PYTHONPATH = Join-Path $config.Tools.paths.kevinBacktesterRepo "prosperity4bt"
            $cmd = @(
                "-m", "prosperity4bt",
                $strategyPath,
                "3-2",
                "--out", $outPath,
                "--data", $dataRoot,
                "--match-trades", $KevinMatchTrades,
                "--no-vis",
                "--no-progress"
            )
            Push-Location $config.Tools.paths.kevinBacktesterRepo
            try {
                $output = & $pythonPath @cmd 2>&1
            }
            finally {
                Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
                Pop-Location
            }
        }
        else {
            Ensure-XeeshanEnvironment
            $pythonPath = Get-VenvPython -VenvDir $config.Tools.envs.xeeshanVenv
            $cmd = @(
                "-m", "prosperity4bt",
                $strategyPath,
                "3-2",
                "--out", $outPath,
                "--data", $dataRoot,
                "--match-trades", $XeeshanMatchTrades,
                "--merge-pnl",
                "--no-progress"
            )
            Push-Location $config.Tools.paths.xeeshanBacktesterRepo
            try {
                $output = & $pythonPath @cmd 2>&1
            }
            finally {
                Pop-Location
            }
        }

        $exitCode = $LASTEXITCODE
        $outputText = ($output | Out-String)
        Set-Content -Path $stdoutPath -Value $outputText -Encoding UTF8
        $total = Get-RunTotal -Text $outputText

        $rows += [pscustomobject]@{
            Strategy          = $strategyName
            Tool              = $toolName
            ExitCode          = $exitCode
            PortalWindowTotal = $total
            RunDirectory      = $runDir
            Stdout            = $stdoutPath
        }

        Write-Host ("{0} {1}: {2}" -f $strategyName, $toolName, $total)
    }
}

$summaryPath = Join-Path $batchDir "summary.csv"
$rows | Export-Csv -Path $summaryPath -NoTypeInformation
Write-Host ("Saved portal-window batch to {0}" -f $batchDir)
