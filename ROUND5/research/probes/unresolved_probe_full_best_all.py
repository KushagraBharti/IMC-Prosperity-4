from __future__ import annotations

from unresolved_probe_portal_best_all import Order, TradingState, Trader as BaseTrader


class Trader(BaseTrader):
    CONFIG = {
        "TRANSLATOR_SPACE_GRAY": ("reversal", 100, 1.00),
        "GALAXY_SOUNDS_SOLAR_WINDS": ("momentum", 100, 0.95),
        "UV_VISOR_ORANGE": ("reversal", 100, 1.00),
        "GALAXY_SOUNDS_DARK_MATTER": ("reversal", 100, 0.95),
        "TRANSLATOR_ASTRO_BLACK": ("reversal", 50, 1.00),
        "MICROCHIP_RECTANGLE": ("reversal", 100, 1.00),
        "TRANSLATOR_VOID_BLUE": ("reversal", 50, 1.00),
        "SLEEP_POD_POLYESTER": ("reversal", 100, 1.00),
        "PANEL_2X4": ("momentum", 50, 0.95),
        "ROBOT_MOPPING": ("momentum", 100, 1.00),
        "SLEEP_POD_NYLON": ("momentum", 100, 1.05),
        "SLEEP_POD_LAMB_WOOL": ("momentum", 50, 1.00),
        "SLEEP_POD_COTTON": ("momentum", 100, 1.00),
        "TRANSLATOR_GRAPHITE_MIST": ("reversal", 100, 0.95),
    }
