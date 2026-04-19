param(
    [ValidateSet("tutorial", "round1", "round2")]
    [string]$Round = "round1"
)

. "$PSScriptRoot\_common.ps1"

$result = Sync-ToolData -Round $Round
Write-Host ("Synced {0} data into:" -f $Round)
Write-Host ("  Kevin mirror:   {0}" -f $result.KevinRoot)
Write-Host ("  Xeeshan mirror: {0}" -f $result.XeeshanRoot)
Write-Host ("  Rust mirror:    {0}" -f $result.RustRoundDir)
