from __future__ import annotations

from unresolved_probe_portal_best_all import Trader as BaseTrader


class Trader(BaseTrader):
    CONFIG = {
        "MICROCHIP_RECTANGLE": ("momentum", 50, 0.90),
        "ROBOT_MOPPING": ("momentum", 50, 0.95),
        "PANEL_2X4": ("momentum", 50, 0.90),
    }
