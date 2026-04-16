param(
    [Parameter(Mandatory = $true)]
    [string]$OfficialArtifact,
    [string]$Round = "",
    [string]$Strategy = ""
)

. "$PSScriptRoot\_common.ps1"

$roundConfig = Get-RoundConfig -Round $Round
$strategyPath = Resolve-StrategyPath -Round $roundConfig.Key -Strategy $Strategy
$artifactPath = (Resolve-Path $OfficialArtifact).Path
$artifactStem = [System.IO.Path]::GetFileNameWithoutExtension($artifactPath)
$investigationRoot = Join-Path (Join-Path (Get-OutputRoot) "investigation") ("official_gap_{0}_{1}" -f $roundConfig.Key, $artifactStem)
$datasetDir = Join-Path $investigationRoot $roundConfig.Key
$analysisDir = Join-Path $investigationRoot "analysis"
$metadataPath = Join-Path $investigationRoot "extract_metadata.json"

New-Item -ItemType Directory -Force -Path $datasetDir | Out-Null
New-Item -ItemType Directory -Force -Path $analysisDir | Out-Null
Remove-Item -LiteralPath (Join-Path $datasetDir "metadata.json") -ErrorAction SilentlyContinue

Write-Host "Extracting official window dataset..."
& python (Join-Path $PSScriptRoot "extract_official_window.py") `
    $artifactPath `
    --round-number $roundConfig.RoundNum `
    --source-round-dir $roundConfig.Root `
    --output-dir $datasetDir `
    --metadata-path $metadataPath

Ensure-XeeshanEnvironment
Ensure-KevinEnvironment

$tooling = Get-ToolingConfig
$xeeshanExe = Join-Path $tooling.Tools.envs.xeeshanVenv "Scripts\prosperity4btx.exe"
$kevinPython = Join-Path $tooling.Tools.envs.kevinVenv "Scripts\python.exe"
$rustCargo = Get-CargoExecutable

$xeeshanModes = @("all", "worse", "none")
$kevinModes = @("all", "worse", "none")

foreach ($mode in $xeeshanModes) {
    $outPath = Join-Path $investigationRoot ("xeeshan_{0}.log" -f $mode)
    Write-Host ("Running Xeeshan ({0})..." -f $mode)
    & $xeeshanExe `
        $strategyPath `
        ("{0}-0" -f $roundConfig.RoundNum) `
        --data $investigationRoot `
        --out $outPath `
        --match-trades $mode `
        --no-progress
}

foreach ($mode in $kevinModes) {
    $outPath = Join-Path $investigationRoot ("kevin_{0}.log" -f $mode)
    Write-Host ("Running Kevin ({0})..." -f $mode)
    Push-Location $tooling.Tools.paths.kevinBacktesterRepo
    try {
        & $kevinPython -m prosperity4bt `
            $strategyPath `
            ("{0}-0" -f $roundConfig.RoundNum) `
            --data $investigationRoot `
            --out $outPath `
            --match-trades $mode `
            --no-vis `
            --no-progress
    }
    finally {
        Pop-Location
    }
}

if ($rustCargo) {
    $rustOutputRoot = Join-Path $investigationRoot "rust_all"
    New-Item -ItemType Directory -Force -Path $rustOutputRoot | Out-Null
    $toolchainDir = Split-Path $rustCargo -Parent
    Write-Host "Running Rust (all)..."
    Push-Location $tooling.Tools.paths.rustBacktesterRepo
    try {
        $env:PATH = ($toolchainDir + ";" + $env:PATH)
        & $rustCargo run -- `
            --trader $strategyPath `
            --dataset $datasetDir `
            --run-id "investigation" `
            --output-root $rustOutputRoot `
            --trade-match-mode all `
            --queue-penetration 1.0 `
            --price-slippage-bps 0.0 `
            --products full `
            --persist `
            --flat `
            --day 0
    }
    finally {
        Pop-Location
    }
}

$officialFillPath = Join-Path $analysisDir "official_fill_patterns.json"
& python (Join-Path $PSScriptRoot "analyze_fill_patterns.py") `
    $artifactPath `
    --round-dir $datasetDir `
    --round-number $roundConfig.RoundNum `
    --day 0 | Set-Content -Path $officialFillPath -Encoding UTF8

foreach ($candidate in @(
        @{ Name = "xeeshan_all"; Path = (Join-Path $investigationRoot "xeeshan_all.log") },
        @{ Name = "kevin_all"; Path = (Join-Path $investigationRoot "kevin_all.log") }
    )) {
    $fillPath = Join-Path $analysisDir ("{0}_fill_patterns.json" -f $candidate.Name)
    $diffPath = Join-Path $analysisDir ("{0}_first_differences.json" -f $candidate.Name)

    & python (Join-Path $PSScriptRoot "analyze_fill_patterns.py") `
        $candidate.Path `
        --round-dir $datasetDir `
        --round-number $roundConfig.RoundNum `
        --day 0 | Set-Content -Path $fillPath -Encoding UTF8

    & python (Join-Path $PSScriptRoot "compare_fill_sequences.py") `
        $artifactPath `
        $candidate.Path | Set-Content -Path $diffPath -Encoding UTF8
}

$rustSubmission = Join-Path $investigationRoot "rust_all\investigation\submission.log"
if (Test-Path $rustSubmission) {
    $rustFillPath = Join-Path $analysisDir "rust_all_fill_patterns.json"
    $rustDiffPath = Join-Path $analysisDir "rust_all_first_differences.json"

    & python (Join-Path $PSScriptRoot "analyze_fill_patterns.py") `
        $rustSubmission `
        --round-dir $datasetDir `
        --round-number $roundConfig.RoundNum `
        --day 0 | Set-Content -Path $rustFillPath -Encoding UTF8

    & python (Join-Path $PSScriptRoot "compare_fill_sequences.py") `
        $artifactPath `
        $rustSubmission | Set-Content -Path $rustDiffPath -Encoding UTF8
}

Write-Host ("Official-gap investigation written to {0}" -f $investigationRoot)
