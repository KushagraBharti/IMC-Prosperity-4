from __future__ import annotations

from unresolved_probe_portal_best_all import Trader as BaseTrader


class Trader(BaseTrader):
    CONFIG = {
        "TRANSLATOR_SPACE_GRAY": ("momentum", 100, 0.90),
        "TRANSLATOR_GRAPHITE_MIST": ("momentum", 100, 1.05),
        "TRANSLATOR_VOID_BLUE": ("reversal", 100, 0.95),
        "TRANSLATOR_ASTRO_BLACK": ("reversal", 100, 0.95),
        "GALAXY_SOUNDS_SOLAR_WINDS": ("momentum", 100, 0.90),
        "GALAXY_SOUNDS_DARK_MATTER": ("reversal", 100, 0.95),
        "UV_VISOR_ORANGE": ("momentum", 100, 0.90),
    }
