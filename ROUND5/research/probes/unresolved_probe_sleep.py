from __future__ import annotations

from unresolved_probe_portal_best_all import Trader as BaseTrader


class Trader(BaseTrader):
    CONFIG = {
        "SLEEP_POD_POLYESTER": ("reversal", 100, 0.90),
        "SLEEP_POD_COTTON": ("reversal", 100, 0.95),
        "SLEEP_POD_LAMB_WOOL": ("momentum", 100, 0.95),
        "SLEEP_POD_NYLON": ("reversal", 100, 1.00),
    }
