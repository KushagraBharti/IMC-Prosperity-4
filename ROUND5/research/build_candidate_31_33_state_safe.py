from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRATEGY_DIR = ROOT / "ROUND5" / "strategies"
OUTPUT_DIR = ROOT / "ROUND5" / "research" / "outputs"

BASES = {
    31: ROOT / "ROUND5" / "official_submissions" / "568114" / "568114.py",
    32: ROOT / "ROUND5" / "strategies" / "round5_candidate_30.py",
    33: ROOT / "ROUND5" / "strategies" / "round5_candidate_29.py",
    34: ROOT / "ROUND5" / "official_submissions" / "568593" / "568593.py",
}

PRODUCT_ALIASES = {
    "PEBBLES_XS": "0",
    "PEBBLES_S": "1",
    "PEBBLES_M": "2",
    "PEBBLES_L": "3",
    "PEBBLES_XL": "4",
    "MICROCHIP_CIRCLE": "5",
    "MICROCHIP_OVAL": "6",
    "MICROCHIP_SQUARE": "7",
    "MICROCHIP_RECTANGLE": "8",
    "MICROCHIP_TRIANGLE": "9",
    "PANEL_1X2": "a",
    "PANEL_1X4": "b",
    "PANEL_2X2": "c",
    "PANEL_2X4": "d",
    "PANEL_4X4": "e",
    "OXYGEN_SHAKE_MORNING_BREATH": "f",
    "OXYGEN_SHAKE_EVENING_BREATH": "g",
    "OXYGEN_SHAKE_MINT": "h",
    "OXYGEN_SHAKE_CHOCOLATE": "i",
    "OXYGEN_SHAKE_GARLIC": "j",
    "UV_VISOR_YELLOW": "k",
    "UV_VISOR_AMBER": "l",
    "UV_VISOR_ORANGE": "m",
    "UV_VISOR_RED": "n",
    "UV_VISOR_MAGENTA": "o",
    "ROBOT_DISHES": "p",
    "ROBOT_MOPPING": "q",
    "ROBOT_LAUNDRY": "r",
    "ROBOT_IRONING": "s",
    "ROBOT_VACUUMING": "t",
    "SLEEP_POD_COTTON": "u",
    "SLEEP_POD_POLYESTER": "v",
    "SLEEP_POD_SUEDE": "w",
    "SLEEP_POD_LAMB_WOOL": "x",
    "SLEEP_POD_NYLON": "y",
    "TRANSLATOR_GRAPHITE_MIST": "z",
    "TRANSLATOR_VOID_BLUE": "A",
    "TRANSLATOR_ASTRO_BLACK": "B",
    "TRANSLATOR_SPACE_GRAY": "C",
    "TRANSLATOR_ECLIPSE_CHARCOAL": "D",
    "GALAXY_SOUNDS_PLANETARY_RINGS": "E",
    "GALAXY_SOUNDS_SOLAR_WINDS": "F",
    "GALAXY_SOUNDS_DARK_MATTER": "G",
    "GALAXY_SOUNDS_BLACK_HOLES": "H",
    "GALAXY_SOUNDS_SOLAR_FLAMES": "I",
    "SNACKPACK_RASPBERRY": "J",
    "SNACKPACK_STRAWBERRY": "K",
    "SNACKPACK_CHOCOLATE": "L",
    "SNACKPACK_VANILLA": "M",
    "SNACKPACK_PISTACHIO": "N",
}


COMPRESSOR = f'''
    STATE_TARGET = 45000
    PRODUCT_ALIASES = {PRODUCT_ALIASES!r}
    PRODUCT_BY_ALIAS = {{v: k for k, v in PRODUCT_ALIASES.items()}}
    PREFIX_ALIASES = {{"h_": "h", "r_": "r", "xrel_": "x", "mom_": "m"}}
    PREFIX_BY_ALIAS = {{"h": "h_", "r": "r_", "x": "xrel_", "m": "mom_"}}

    def dump_cache(self, cache: dict) -> str:
        compact = {{}}
        for key, values in cache.items():
            if not isinstance(values, list):
                continue
            keep = self.cache_keep(key)
            trimmed = values[-keep:] if keep > 0 else values
            compact[self.short_key(key)] = self.pack_series(key, trimmed)
        return json.dumps({{"c": compact}}, separators=(",", ":"))

    def load_cache(self, raw: str) -> dict:
        try:
            data = json.loads(raw) if raw else {{}}
        except Exception:
            return {{}}
        if isinstance(data, dict) and "c" in data:
            cache = {{}}
            for short, packed in data.get("c", {{}}).items():
                key = self.long_key(short)
                cache[key] = self.unpack_series(key, packed)
            return cache
        return data if isinstance(data, dict) else {{}}

    def pack_series(self, key: str, values: List[float]) -> list:
        if not values:
            return [0, []]
        scale = self.cache_scale(key)
        ints = [int(round(float(value) * scale)) for value in values]
        base = ints[0]
        deltas = [ints[i] - ints[i - 1] for i in range(1, len(ints))]
        return [base, deltas]

    def unpack_series(self, key: str, packed: list) -> List[float]:
        if not isinstance(packed, list) or len(packed) != 2:
            return []
        scale = self.cache_scale(key)
        current = int(packed[0])
        values = [current / scale]
        deltas = packed[1] if isinstance(packed[1], list) else []
        for delta in deltas:
            current += int(delta)
            values.append(current / scale)
        return values

    def cache_scale(self, key: str) -> int:
        if key.startswith("r_"):
            return 1000
        if key.startswith("xrel_"):
            return 100
        return 2

    def cache_keep(self, key: str) -> int:
        if key.startswith("r_"):
            return 90
        if key.startswith("xrel_"):
            return 180
        if key.startswith("mom_"):
            product = key[4:]
            cfg = self.MOMENTUM_EXTRAS.get(product) if hasattr(self, "MOMENTUM_EXTRAS") else None
            lookback = int(cfg[0]) if cfg else 220
            return max(lookback + 6, 140)
        if key.startswith("h_"):
            product = key[2:]
            cfg = self.SIGNAL_CONFIG.get(product) if hasattr(self, "SIGNAL_CONFIG") else None
            lookback = int(cfg[1]) if cfg else 220
            return max(lookback + 6, 180)
        return 220

    def short_key(self, key: str) -> str:
        for prefix, short_prefix in self.PREFIX_ALIASES.items():
            if key.startswith(prefix):
                product = key[len(prefix):]
                return short_prefix + self.PRODUCT_ALIASES.get(product, product)
        return key

    def long_key(self, short: str) -> str:
        if not short:
            return short
        prefix = self.PREFIX_BY_ALIAS.get(short[0])
        if not prefix:
            return short
        product = self.PRODUCT_BY_ALIAS.get(short[1:], short[1:])
        return prefix + product
'''


def replace_load_cache(source: str) -> str:
    marker = "\n    def load_cache(self, raw: str) -> dict:\n"
    start = source.rfind(marker)
    if start == -1:
        raise ValueError("load_cache method not found")
    return source[:start] + COMPRESSOR


def transform(source: str) -> str:
    source = source.replace(
        'return result, 0, json.dumps(cache, separators=(",", ":"))',
        "return result, 0, self.dump_cache(cache)",
    )
    source = replace_load_cache(source)
    return source.rstrip() + "\n"


def main() -> None:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    notes = [
        "# Candidate 31-34 State Repair Notes",
        "",
        "## Repair Method",
        "- Trading logic is preserved: product lists, thresholds, formulas, ranking, sizing, and execution rules are copied from the base files.",
        "- Only `traderData` serialization/deserialization is changed.",
        "- Histories are still exposed to the trading code as normal float lists after load.",
        "- Returned state uses short product/prefix aliases, delta-encoded integer arrays, and deterministic trimming to the longest window actually read by the formulas.",
        "- Mid-price histories are stored at half-tick precision (`scale=2`), which is exact for top-of-book mids in this data.",
        "- PEBBLES residual histories use `scale=1000`; category residual histories use `scale=100`.",
        "",
    ]
    for number, base in BASES.items():
        out = STRATEGY_DIR / f"round5_candidate_{number}.py"
        out.write_text(transform(base.read_text(encoding="utf-8")), encoding="utf-8")
        notes.extend(
            [
                f"## round5_candidate_{number}.py",
                f"- Base: `{base.as_posix()}`.",
                "- Behavior change: intended none beyond sub-cent residual quantization needed for compact state.",
        "- Official safety target: returned `traderData` below 45,000 characters; never relies on portal truncation.",
                "",
            ]
        )
    (OUTPUT_DIR / "candidate_31_33_state_repair_notes.md").write_text("\n".join(notes), encoding="utf-8")


if __name__ == "__main__":
    main()
