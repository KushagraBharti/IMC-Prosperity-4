param(
    [int[]]$Days,
    [string]$Strategy = "",
    [ValidateSet("all", "worse", "none")]
    [string]$MatchTrades = "worse",
    [switch]$PrintTraderOutput
)

& "$PSScriptRoot\bt-kevin.ps1" -Round round2 -Days $Days -Strategy $Strategy -MatchTrades $MatchTrades -PrintTraderOutput:$PrintTraderOutput
