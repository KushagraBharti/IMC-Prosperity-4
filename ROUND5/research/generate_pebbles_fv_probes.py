from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = ROOT / "ROUND5" / "research" / "probes" / "150k_exec"
ROBUST_BASE = PROBE_DIR / "probe_c35_anchor_both_micro_uv_conservative.py"
PORTAL_BASE = PROBE_DIR / "probe_increment_vanilla_micro_uv_loose.py"


QUADRATIC_METHOD = r'''
    def fit_predict(self, xs: List[float], ys: List[float], x0: float) -> float:
        n = len(xs)
        sx = sum(xs)
        sx2 = sum(x * x for x in xs)
        sx3 = sum(x * x * x for x in xs)
        sx4 = sum(x * x * x * x for x in xs)
        sy = sum(ys)
        sxy = sum(xs[i] * ys[i] for i in range(n))
        sx2y = sum(xs[i] * xs[i] * ys[i] for i in range(n))
        a = [[n, sx, sx2], [sx, sx2, sx3], [sx2, sx3, sx4]]
        b = [sy, sxy, sx2y]
        # Tiny 3x3 Gaussian elimination, no dependencies.
        for i in range(3):
            pivot = i
            for r in range(i + 1, 3):
                if abs(a[r][i]) > abs(a[pivot][i]):
                    pivot = r
            if abs(a[pivot][i]) < 1e-9:
                return self.fit_predict_linear(xs, ys, x0)
            if pivot != i:
                a[i], a[pivot] = a[pivot], a[i]
                b[i], b[pivot] = b[pivot], b[i]
            div = a[i][i]
            for c in range(i, 3):
                a[i][c] /= div
            b[i] /= div
            for r in range(3):
                if r == i:
                    continue
                mul = a[r][i]
                for c in range(i, 3):
                    a[r][c] -= mul * a[i][c]
                b[r] -= mul * b[i]
        return b[0] + b[1] * x0 + b[2] * x0 * x0

    def fit_predict_linear(self, xs: List[float], ys: List[float], x0: float) -> float:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        den = sum((x - mx) ** 2 for x in xs)
        if den <= 1e-9:
            return my
        slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs))) / den
        return my + slope * (x0 - mx)
'''


def replace_method(text: str, new_method: str) -> str:
    start = text.index("    def fit_predict")
    end = text.index("    def improve_bid", start)
    return text[:start] + new_method + "\n\n" + text[end:]


def replace_literal(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing literal {old!r}")
    return text.replace(old, new, 1)


def write_probe(name: str, text: str) -> None:
    text = text.replace("class Trader:", f"# Temporary PEBBLES fair-value probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def variants(base_name: str, base_text: str) -> None:
    quad = replace_method(base_text, QUADRATIC_METHOD)
    write_probe(f"probe_peb_{base_name}_quadratic", quad)

    aggressive = quad
    aggressive = replace_literal(aggressive, "'PEBBLES_XS': 1.02", "'PEBBLES_XS': 1.16")
    aggressive = replace_literal(aggressive, "'PEBBLES_M': 1.18", "'PEBBLES_M': 1.28")
    aggressive = replace_literal(aggressive, "'PEBBLES_L': 1.08", "'PEBBLES_L': 1.22")
    aggressive = replace_literal(aggressive, "PEB_AGGRESSION = 1.08", "PEB_AGGRESSION = 1.24")
    write_probe(f"probe_peb_{base_name}_quadratic_aggressive_mxl", aggressive)

    passive = aggressive
    passive = replace_literal(passive, "PEB_ALLOW_TAKE = 1", "PEB_ALLOW_TAKE = 0")
    write_probe(f"probe_peb_{base_name}_quadratic_passive_mxl", passive)

    taker = aggressive
    taker = replace_literal(taker, "abs(book[\"mid\"] - fair) > max(10.5, 1.85 * rvol)", "abs(book[\"mid\"] - fair) > max(7.5, 1.35 * rvol)")
    taker = replace_literal(taker, "edge_floor + 5.8", "edge_floor + 3.8")
    write_probe(f"probe_peb_{base_name}_quadratic_taker_mxl", taker)


def main() -> None:
    variants("robust", ROBUST_BASE.read_text(encoding="utf-8"))
    variants("portal", PORTAL_BASE.read_text(encoding="utf-8"))
    print(f"Wrote PEBBLES FV probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
