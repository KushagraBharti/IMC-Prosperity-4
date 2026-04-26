from __future__ import annotations

import importlib.util
from pathlib import Path


_spec = importlib.util.spec_from_file_location("_round3_base", Path(__file__).with_name("current_trader.py"))
_module = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_module)


class Trader(_module.Trader):
    ENABLE_HYDROGEL = True
    ENABLE_OPTIONS = True
    ENABLE_HEDGE = False
    ENABLE_VELVET_MM = True
    HYDROGEL_AGGRESSION = 1.00
    OPTION_AGGRESSION = 1.00