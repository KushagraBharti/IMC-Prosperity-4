Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Read-JsonConfig {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-Content -Raw -Path $Path | ConvertFrom-Json)
}

function Get-ToolingConfig {
    $root = Get-ProjectRoot
    return [pscustomobject]@{
        ProjectRoot = $root
        Defaults    = Read-JsonConfig (Join-Path $root "config\defaults.json")
        Datasets    = Read-JsonConfig (Join-Path $root "config\datasets.json")
        Tools       = Read-JsonConfig (Join-Path $root "config\tools.local.json")
    }
}

function Normalize-RoundKey {
    param([string]$Round)

    if ([string]::IsNullOrWhiteSpace($Round)) {
        return $null
    }

    $normalized = $Round.Trim().ToLowerInvariant()
    switch ($normalized) {
        "0" { return "tutorial" }
        "round0" { return "tutorial" }
        "tutorial_round" { return "tutorial" }
        "tutorial" { return "tutorial" }
        "1" { return "round1" }
        "round1" { return "round1" }
        "round_1" { return "round1" }
        "2" { return "round2" }
        "round2" { return "round2" }
        "round_2" { return "round2" }
        "3" { return "round3" }
        "round3" { return "round3" }
        "round_3" { return "round3" }
        default { return $normalized }
    }
}

function Get-RoundConfig {
    param(
        [Parameter(Mandatory = $false)][string]$Round
    )

    $config = Get-ToolingConfig
    $roundKey = Normalize-RoundKey $Round
    if ([string]::IsNullOrWhiteSpace($roundKey)) {
        $roundKey = Normalize-RoundKey $config.Defaults.activeRound
    }

    $roundConfig = $config.Datasets.rounds.PSObject.Properties[$roundKey]
    if ($null -eq $roundConfig) {
        throw "Unknown round key '$Round'. Valid values: tutorial, round1, round2, round3."
    }

    return [pscustomobject]@{
        Key      = $roundKey
        Root     = $roundConfig.Value.root
        Label    = $roundConfig.Value.label
        RoundNum = [int]$roundConfig.Value.roundNumber
        Current  = $roundConfig.Value.strategyCurrent
        Archive  = $roundConfig.Value.strategyArchiveDir
        Official = $roundConfig.Value.officialSubmissionDir
        Project  = $config.ProjectRoot
        Defaults = $config.Defaults
        Tools    = $config.Tools
    }
}

function Get-RoundCsvFiles {
    param([Parameter(Mandatory = $true)][pscustomobject]$RoundConfig)

    $pricesPattern = "prices_round_{0}_day_*.csv" -f $RoundConfig.RoundNum
    $tradesPattern = "trades_round_{0}_day_*.csv" -f $RoundConfig.RoundNum

    $prices = Get-ChildItem -Path $RoundConfig.Root -Filter $pricesPattern -File | Sort-Object Name
    $trades = Get-ChildItem -Path $RoundConfig.Root -Filter $tradesPattern -File | Sort-Object Name

    return [pscustomobject]@{
        Prices = $prices
        Trades = $trades
    }
}

function Get-OutputRoot {
    $config = Get-ToolingConfig
    return $config.Defaults.outputRoot
}

function New-RunDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Kind,
        [Parameter(Mandatory = $true)][string]$Tool,
        [Parameter(Mandatory = $true)][string]$Round,
        [Parameter(Mandatory = $false)][string]$Label
    )

    $root = Get-OutputRoot
    $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
    $safeLabel = if ([string]::IsNullOrWhiteSpace($Label)) { $null } else { $Label.Replace(" ", "_") }
    $name = if ($null -eq $safeLabel) {
        "{0}_{1}_{2}" -f $timestamp, $Tool, $Round
    }
    else {
        "{0}_{1}_{2}_{3}" -f $timestamp, $Tool, $Round, $safeLabel
    }

    $path = Join-Path (Join-Path $root $Kind) $name
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    return $path
}

function Get-VenvPython {
    param([Parameter(Mandatory = $true)][string]$VenvDir)
    return (Join-Path $VenvDir "Scripts\python.exe")
}

function Ensure-UvVenv {
    param(
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [Parameter(Mandatory = $true)][string]$VenvDir
    )

    $pythonPath = Get-VenvPython -VenvDir $VenvDir
    $desiredVersion = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    $needsRecreate = $false

    if (Test-Path $pythonPath) {
        $existingVersion = (& $pythonPath -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if ($existingVersion.Trim() -ne $desiredVersion.Trim()) {
            $needsRecreate = $true
        }
    }

    if ($needsRecreate -and (Test-Path $VenvDir)) {
        Remove-Item -Recurse -Force -LiteralPath $VenvDir
    }

    if (-not (Test-Path $pythonPath)) {
        Push-Location $RepoPath
        try {
            & uv venv --python python $VenvDir | Out-Host
        }
        finally {
            Pop-Location
        }
    }
}

function Ensure-XeeshanEnvironment {
    $config = Get-ToolingConfig
    $repo = $config.Tools.paths.xeeshanBacktesterRepo
    $venv = $config.Tools.envs.xeeshanVenv
    Ensure-UvVenv -RepoPath $repo -VenvDir $venv

    $pythonPath = Get-VenvPython -VenvDir $venv
    if (-not (Test-Path (Join-Path $venv "Scripts\prosperity4btx.exe"))) {
        Push-Location $repo
        try {
            & uv sync --no-dev | Out-Host
            & uv pip install --python $pythonPath -e . | Out-Host
        }
        finally {
            Pop-Location
        }
    }
}

function Ensure-KevinEnvironment {
    $config = Get-ToolingConfig
    $repo = $config.Tools.paths.kevinBacktesterRepo
    $venv = $config.Tools.envs.kevinVenv
    Ensure-UvVenv -RepoPath $repo -VenvDir $venv

    $pythonPath = Get-VenvPython -VenvDir $venv
    if (-not (Test-Path (Join-Path $venv "Scripts\typer.exe"))) {
        & uv pip install --python $pythonPath ipython jsonpickle orjson tqdm typer | Out-Host
    }
}

function Ensure-ChrisEnvironment {
    $config = Get-ToolingConfig
    $repo = Join-Path $config.Tools.paths.chrisMonteCarloRepo "backtester"
    $venv = $config.Tools.envs.chrisVenv
    Ensure-UvVenv -RepoPath $repo -VenvDir $venv

    $pythonPath = Get-VenvPython -VenvDir $venv
    if (-not (Test-Path (Join-Path $venv "Scripts\prosperity4mcbt.exe"))) {
        Push-Location $repo
        try {
            & uv sync --no-dev | Out-Host
            & uv pip install --python $pythonPath -e . | Out-Host
        }
        finally {
            Pop-Location
        }
    }
}

function Ensure-KevinVisualizerDependencies {
    $config = Get-ToolingConfig
    $repo = $config.Tools.paths.kevinVisualizerRepo
    if (-not (Test-Path (Join-Path $repo "node_modules"))) {
        Push-Location $repo
        try {
            & npm install | Out-Host
        }
        finally {
            Pop-Location
        }
    }
}

function Ensure-GsgillVisualizerDependencies {
    $config = Get-ToolingConfig
    $repo = $config.Tools.paths.gsgillVisualizerRepo
    if (-not (Test-Path (Join-Path $repo "node_modules"))) {
        Push-Location $repo
        try {
            & npm install | Out-Host
        }
        finally {
            Pop-Location
        }
    }
}

function Get-CargoExecutable {
    $command = Get-Command cargo -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $fallbacks = @(
        "$env:LOCALAPPDATA\puccinialin\puccinialin\Cache\rustup\toolchains\stable-x86_64-pc-windows-msvc\bin\cargo.exe",
        "$env:LOCALAPPDATA\puccinialin\puccinialin\Cache\cargo\bin\cargo.exe",
        "$env:USERPROFILE\.cargo\bin\cargo.exe"
    )

    foreach ($candidate in $fallbacks) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Sync-ToolData {
    param([Parameter(Mandatory = $true)][string]$Round)

    $roundConfig = Get-RoundConfig -Round $Round
    $csvFiles = Get-RoundCsvFiles -RoundConfig $roundConfig
    $outputRoot = Get-OutputRoot

    $kevinTarget = Join-Path $outputRoot ("tool-data\kevin\round{0}" -f $roundConfig.RoundNum)
    $xeeshanTarget = Join-Path $outputRoot ("tool-data\xeeshan\round{0}" -f $roundConfig.RoundNum)
    $rustTarget = Join-Path $outputRoot ("tool-data\rust\round{0}" -f $roundConfig.RoundNum)

    New-Item -ItemType Directory -Force -Path $kevinTarget, $xeeshanTarget, $rustTarget | Out-Null

    foreach ($file in @($csvFiles.Prices + $csvFiles.Trades)) {
        Copy-Item -Force -Path $file.FullName -Destination (Join-Path $kevinTarget $file.Name)
        Copy-Item -Force -Path $file.FullName -Destination (Join-Path $xeeshanTarget $file.Name)
        Copy-Item -Force -Path $file.FullName -Destination (Join-Path $rustTarget $file.Name)
    }

    return [pscustomobject]@{
        KevinRoot   = (Join-Path $outputRoot "tool-data\kevin")
        XeeshanRoot = (Join-Path $outputRoot "tool-data\xeeshan")
        RustRoundDir = $rustTarget
    }
}

function Resolve-StrategyPath {
    param(
        [Parameter(Mandatory = $true)][string]$Round,
        [Parameter(Mandatory = $false)][string]$Strategy
    )

    if (-not [string]::IsNullOrWhiteSpace($Strategy)) {
        return (Resolve-Path $Strategy).Path
    }

    $roundConfig = Get-RoundConfig -Round $Round
    return (Resolve-Path $roundConfig.Current).Path
}

function Convert-DayArgs {
    param(
        [Parameter(Mandatory = $true)][pscustomobject]$RoundConfig,
        [Parameter(Mandatory = $false)][int[]]$Days
    )

    if ($null -eq $Days -or $Days.Count -eq 0) {
        return @([string]$RoundConfig.RoundNum)
    }

    $args = @()
    foreach ($day in $Days) {
        $args += "{0}-{1}" -f $RoundConfig.RoundNum, $day
    }

    return $args
}

function Write-LatestRunPointers {
    param(
        [Parameter(Mandatory = $true)][string]$Tool,
        [Parameter(Mandatory = $true)][string]$Round,
        [Parameter(Mandatory = $true)][string]$RunDir,
        [Parameter(Mandatory = $true)][string]$LogPath,
        [Parameter(Mandatory = $false)][string]$StrategyPath
    )

    $config = Get-ToolingConfig
    $latestLog = $config.Defaults.latestLogPath
    $latestRunInfo = $config.Defaults.latestRunInfoPath

    Copy-Item -Force -Path $LogPath -Destination $latestLog

    $payload = [ordered]@{
        tool         = $Tool
        round        = $Round
        runDirectory = $RunDir
        logPath      = $LogPath
        strategyPath = $StrategyPath
        updatedAt    = (Get-Date).ToString("o")
    } | ConvertTo-Json -Depth 8

    Set-Content -Path $latestRunInfo -Value $payload -Encoding UTF8
}

function Get-LatestRunInfo {
    $config = Get-ToolingConfig
    $path = $config.Defaults.latestRunInfoPath
    if (-not (Test-Path $path)) {
        throw "No latest run metadata found at $path. Run a backtester first."
    }

    return Read-JsonConfig -Path $path
}

function Get-OfficialBundleDirectories {
    param([Parameter(Mandatory = $true)][string]$Round)

    $roundConfig = Get-RoundConfig -Round $Round
    $legacyDirs = Get-ChildItem -Path $roundConfig.Root -Directory | Where-Object { $_.Name -match '^\d+$' }
    $managedDirs = @()
    if (Test-Path $roundConfig.Official) {
        $managedDirs = Get-ChildItem -Path $roundConfig.Official -Directory
    }

    return @($legacyDirs + $managedDirs | Sort-Object FullName -Unique)
}
