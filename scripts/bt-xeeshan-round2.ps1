param(
    [int[]]$Days,
    [string]$Strategy = "",
    [ValidateSet("all", "worse", "none")]
    [string]$MatchTrades = "all",
    [switch]$PrintTraderOutput
)

& "$PSScriptRoot\bt-xeeshan.ps1" -Round round2 -Days $Days -Strategy $Strategy -MatchTrades $MatchTrades -PrintTraderOutput:$PrintTraderOutput
