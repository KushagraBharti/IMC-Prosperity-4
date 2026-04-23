param(
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

& "$PSScriptRoot\bt-rust.ps1" -Round round2 -Days $Days -Strategy $Strategy -TradeMatchMode $TradeMatchMode -QueuePenetration $QueuePenetration -PriceSlippageBps $PriceSlippageBps -Products $Products -Carry:$Carry
