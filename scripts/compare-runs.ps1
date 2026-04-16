param(
    [Parameter(Mandatory = $true)][string]$Left,
    [Parameter(Mandatory = $true)][string]$Right
)

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
python (Join-Path $projectRoot "scripts\compare_runs.py") $Left $Right
