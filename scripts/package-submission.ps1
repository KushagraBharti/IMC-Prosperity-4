param(
    [string]$Round = "",
    [string]$Strategy = "",
    [string]$Label = ""
)

. "$PSScriptRoot\_common.ps1"

$roundConfig = Get-RoundConfig -Round $Round
$strategyPath = Resolve-StrategyPath -Round $roundConfig.Key -Strategy $Strategy
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$slug = if ([string]::IsNullOrWhiteSpace($Label)) { "submission" } else { $Label.Replace(" ", "_") }
$fileName = "{0}_{1}_{2}.py" -f $timestamp, $roundConfig.Key, $slug

$archivePath = Join-Path $roundConfig.Archive $fileName
$outputPath = Join-Path (Join-Path (Get-OutputRoot) "submissions") $fileName

Copy-Item -Force -Path $strategyPath -Destination $archivePath
Copy-Item -Force -Path $strategyPath -Destination $outputPath

Write-Host ("Archived strategy to {0}" -f $archivePath)
Write-Host ("Submission-ready copy at {0}" -f $outputPath)
