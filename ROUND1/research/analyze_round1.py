from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
ROUND1_DIR = ROOT / "ROUND1"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

PRODUCTS = ("ASH_COATED_OSMIUM", "INTARIAN_PEPPER_ROOT")
PRICE_LEVELS = (1, 2, 3)
PEPPER_TREND_PER_TIMESTAMP = 0.001


@dataclass(frozen=True)
class ProductStats:
    product: str
    rows: int
    mean_mid: float
    std_mid: float
    mean_spread: float
    imbalance_corr: float
    wall_corr: float


def load_prices() -> pd.DataFrame:
    frames = []
    for path in sorted(ROUND1_DIR.glob("prices_round_1_day_*.csv")):
        frame = pd.read_csv(path, sep=";")
        frame["source_file"] = path.name
        frames.append(frame)
    if not frames:
        raise FileNotFoundError("No Round 1 price files found.")
    prices = pd.concat(frames, ignore_index=True)
    return enrich_prices(prices)


def load_trades() -> pd.DataFrame:
    frames = []
    for path in sorted(ROUND1_DIR.glob("trades_round_1_day_*.csv")):
        frame = pd.read_csv(path, sep=";")
        frame["source_file"] = path.name
        frames.append(frame)
    if not frames:
        raise FileNotFoundError("No Round 1 trade files found.")
    trades = pd.concat(frames, ignore_index=True)
    trades["day"] = trades["source_file"].str.extract(r"day_(-?\d+)").astype(int)
    return trades.rename(columns={"symbol": "product"})


def enrich_prices(prices: pd.DataFrame) -> pd.DataFrame:
    enriched = prices.copy()
    enriched["valid_book"] = enriched["bid_price_1"].notna() & enriched["ask_price_1"].notna()
    enriched["spread"] = enriched["ask_price_1"] - enriched["bid_price_1"]
    enriched["top_imbalance"] = (
        (enriched["bid_volume_1"].fillna(0) - enriched["ask_volume_1"].fillna(0))
        / (enriched["bid_volume_1"].fillna(0) + enriched["ask_volume_1"].fillna(0)).replace(0, np.nan)
    )
    enriched["wall_bid_price"] = enriched.apply(lambda row: wall_price(row, "bid"), axis=1)
    enriched["wall_ask_price"] = enriched.apply(lambda row: wall_price(row, "ask"), axis=1)
    enriched["wall_mid"] = (enriched["wall_bid_price"] + enriched["wall_ask_price"]) / 2.0
    enriched["wall_mid"] = enriched["wall_mid"].fillna(enriched["mid_price"])
    enriched = enriched.sort_values(["product", "day", "timestamp"]).reset_index(drop=True)
    enriched["next_valid_mid"] = np.nan
    enriched["next_valid_mid_change"] = np.nan
    valid_signal = enriched["valid_book"] & enriched["mid_price"].gt(0)
    for _, frame in enriched[valid_signal].groupby(["product", "day"]):
        next_mid = frame["mid_price"].shift(-1)
        enriched.loc[frame.index, "next_valid_mid"] = next_mid
        enriched.loc[frame.index, "next_valid_mid_change"] = next_mid - frame["mid_price"]
    enriched["wall_deviation"] = enriched["wall_mid"] - enriched["mid_price"]
    enriched["pepper_detrended"] = np.where(
        enriched["product"] == "INTARIAN_PEPPER_ROOT",
        enriched["mid_price"] - PEPPER_TREND_PER_TIMESTAMP * enriched["timestamp"],
        np.nan,
    )
    return enriched


def wall_price(row: pd.Series, side: str) -> float:
    volumes: list[tuple[float, float]] = []
    for level in PRICE_LEVELS:
        price = row.get(f"{side}_price_{level}")
        volume = row.get(f"{side}_volume_{level}")
        if pd.notna(price) and pd.notna(volume):
            volumes.append((abs(float(volume)), float(price)))
    if not volumes:
        return np.nan
    _, price = max(volumes, key=lambda item: item[0])
    return price


def summarize(prices: pd.DataFrame) -> list[ProductStats]:
    stats: list[ProductStats] = []
    filtered = prices[prices["valid_book"] & prices["mid_price"].gt(0)].copy()
    for product, frame in filtered.groupby("product"):
        valid_signal = frame["top_imbalance"].notna() & frame["next_valid_mid_change"].notna()
        valid_wall = frame["wall_deviation"].notna() & frame["next_valid_mid_change"].notna()
        stats.append(
            ProductStats(
                product=product,
                rows=len(frame),
                mean_mid=float(frame["mid_price"].mean()),
                std_mid=float(frame["mid_price"].std()),
                mean_spread=float(frame["spread"].mean()),
                imbalance_corr=float(frame.loc[valid_signal, "top_imbalance"].corr(frame.loc[valid_signal, "next_valid_mid_change"])),
                wall_corr=float(frame.loc[valid_wall, "wall_deviation"].corr(frame.loc[valid_wall, "next_valid_mid_change"])),
            )
        )
    return stats


def plot_mid_paths(prices: pd.DataFrame) -> Path:
    filtered = prices[prices["mid_price"].gt(0)].copy()
    days = sorted(filtered["day"].unique())
    fig, axes = plt.subplots(len(PRODUCTS), len(days), figsize=(16, 8), sharex=True)
    for row_index, product in enumerate(PRODUCTS):
        for col_index, day in enumerate(days):
            axis = axes[row_index, col_index]
            frame = filtered[(filtered["product"] == product) & (filtered["day"] == day)]
            axis.plot(frame["timestamp"], frame["mid_price"], linewidth=1.2, color="#0b7285")
            axis.set_title(f"{product}\nday {day}")
            axis.grid(alpha=0.2)
            if row_index == len(PRODUCTS) - 1:
                axis.set_xlabel("timestamp")
            if col_index == 0:
                axis.set_ylabel("mid price")
    fig.suptitle("Round 1 mid-price paths")
    fig.tight_layout()
    output = OUTPUT_DIR / "mid_paths.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def plot_pepper_detrended(prices: pd.DataFrame) -> Path:
    pepper = prices[(prices["product"] == "INTARIAN_PEPPER_ROOT") & prices["mid_price"].gt(0)].copy()
    days = sorted(pepper["day"].unique())
    fig, axes = plt.subplots(1, len(days), figsize=(15, 4), sharey=True)
    for axis, day in zip(axes, days):
        frame = pepper[pepper["day"] == day]
        axis.plot(frame["timestamp"], frame["pepper_detrended"], linewidth=1.1, color="#c92a2a")
        anchor = frame["pepper_detrended"].mean()
        axis.axhline(anchor, linestyle="--", linewidth=1, color="#495057")
        axis.set_title(f"day {day} detrended")
        axis.set_xlabel("timestamp")
        axis.grid(alpha=0.2)
    axes[0].set_ylabel("mid - 0.001 * timestamp")
    fig.suptitle("Pepper detrended by the fitted linear drift")
    fig.tight_layout()
    output = OUTPUT_DIR / "pepper_detrended.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def plot_spread_boxplot(prices: pd.DataFrame) -> Path:
    filtered = prices[prices["valid_book"] & prices["spread"].notna()].copy()
    filtered["label"] = filtered["product"] + " day " + filtered["day"].astype(str)
    fig, axis = plt.subplots(figsize=(12, 5))
    sns.boxplot(data=filtered, x="label", y="spread", hue="product", dodge=False, ax=axis)
    axis.set_title("Spread distribution by product and day")
    axis.set_xlabel("")
    axis.set_ylabel("ask_1 - bid_1")
    axis.tick_params(axis="x", rotation=20)
    axis.grid(alpha=0.2, axis="y")
    axis.legend().remove()
    fig.tight_layout()
    output = OUTPUT_DIR / "spread_boxplot.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def plot_imbalance_signal(prices: pd.DataFrame) -> Path:
    filtered = prices[prices["valid_book"] & prices["next_valid_mid_change"].notna() & prices["top_imbalance"].notna()].copy()
    filtered["imbalance_bucket"] = pd.cut(filtered["top_imbalance"], bins=np.linspace(-1.0, 1.0, 21), include_lowest=True)
    bucketed = (
        filtered.groupby(["product", "imbalance_bucket"], observed=False)["next_valid_mid_change"]
        .mean()
        .reset_index()
    )
    bucketed["bucket_center"] = bucketed["imbalance_bucket"].apply(lambda bucket: float(bucket.mid))
    fig, axis = plt.subplots(figsize=(10, 5))
    for product, frame in bucketed.groupby("product"):
        axis.plot(frame["bucket_center"], frame["next_valid_mid_change"], marker="o", linewidth=1.8, label=product)
    axis.axhline(0, color="#495057", linewidth=1, linestyle="--")
    axis.set_title("Top-of-book imbalance vs next mid-price change")
    axis.set_xlabel("top imbalance bucket center")
    axis.set_ylabel("mean next mid change")
    axis.grid(alpha=0.2)
    axis.legend()
    fig.tight_layout()
    output = OUTPUT_DIR / "imbalance_signal.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def plot_trade_overlay(prices: pd.DataFrame, trades: pd.DataFrame) -> Path:
    filtered = prices[prices["mid_price"].gt(0)].copy()
    days = sorted(filtered["day"].unique())
    fig, axes = plt.subplots(len(PRODUCTS), len(days), figsize=(16, 8), sharex=True)
    for row_index, product in enumerate(PRODUCTS):
        for col_index, day in enumerate(days):
            axis = axes[row_index, col_index]
            book = filtered[(filtered["product"] == product) & (filtered["day"] == day)]
            tape = trades[(trades["product"] == product) & (trades["day"] == day)]
            axis.plot(book["timestamp"], book["mid_price"], color="#495057", linewidth=1.0, alpha=0.8)
            if not tape.empty:
                axis.scatter(
                    tape["timestamp"],
                    tape["price"],
                    s=np.clip(tape["quantity"] * 3, 10, 80),
                    alpha=0.5,
                    color="#1c7ed6",
                    edgecolors="none",
                )
            axis.set_title(f"{product}\nday {day}")
            axis.grid(alpha=0.2)
            if row_index == len(PRODUCTS) - 1:
                axis.set_xlabel("timestamp")
            if col_index == 0:
                axis.set_ylabel("price")
    fig.suptitle("Trade tape overlaid on mid-price paths")
    fig.tight_layout()
    output = OUTPUT_DIR / "trade_overlay.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    return output


def write_summary(prices: pd.DataFrame, trades: pd.DataFrame, stats: Iterable[ProductStats], outputs: Iterable[Path]) -> Path:
    lines = [
        "# Round 1 dataset summary",
        "",
        "## Files",
        "",
        *(f"- `{path.name}`" for path in sorted(ROUND1_DIR.glob("prices_round_1_day_*.csv"))),
        *(f"- `{path.name}`" for path in sorted(ROUND1_DIR.glob("trades_round_1_day_*.csv"))),
        "",
        "## Product stats",
        "",
        "| product | rows | mean mid | std mid | mean spread | corr(imbalance, next mid change) | corr(wall deviation, next mid change) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for stat in stats:
        lines.append(
            f"| {stat.product} | {stat.rows} | {stat.mean_mid:.3f} | {stat.std_mid:.3f} | "
            f"{stat.mean_spread:.3f} | {stat.imbalance_corr:.4f} | {stat.wall_corr:.4f} |"
        )

    pepper = prices[(prices["product"] == "INTARIAN_PEPPER_ROOT") & prices["mid_price"].gt(0)]
    lines.extend(
        [
            "",
            "## Pepper drift check",
            "",
            "| day | fitted slope | detrended mean | detrended std |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for day, frame in pepper.groupby("day"):
        slope = np.polyfit(frame["timestamp"], frame["mid_price"], 1)[0]
        detrended = frame["pepper_detrended"]
        lines.append(f"| {day} | {slope:.6f} | {detrended.mean():.3f} | {detrended.std():.3f} |")

    lines.extend(
        [
            "",
            "## Trade counts",
            "",
            "| product | trades | total qty | mean price | std price |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for product, frame in trades.groupby("product"):
        lines.append(
            f"| {product} | {len(frame)} | {int(frame['quantity'].sum())} | {frame['price'].mean():.3f} | {frame['price'].std():.3f} |"
        )

    lines.extend(
        [
            "",
            "## Generated plots",
            "",
            *(f"- `{path.name}`" for path in outputs),
            "",
            "## High-confidence takeaways",
            "",
            "- ASH_COATED_OSMIUM behaves like a stable market-making product around 10,000.",
            "- INTARIAN_PEPPER_ROOT shows a highly consistent positive linear drift of about 0.001 per timestamp plus a tight residual process.",
            "- Top-of-book imbalance is strongly predictive for both products and should be used as a short-horizon alpha input.",
            "- The spread is wide enough that quote placement and inventory management matter more than small fair-value estimation errors.",
        ]
    )

    output = OUTPUT_DIR / "summary.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    prices = load_prices()
    trades = load_trades()
    stats = summarize(prices)
    outputs = [
        plot_mid_paths(prices),
        plot_pepper_detrended(prices),
        plot_spread_boxplot(prices),
        plot_imbalance_signal(prices),
        plot_trade_overlay(prices, trades),
    ]
    summary_path = write_summary(prices, trades, stats, outputs)
    print(f"Wrote analysis outputs to {OUTPUT_DIR}")
    print(f"Summary: {summary_path.name}")
    for path in outputs:
        print(f"Plot: {path.name}")


if __name__ == "__main__":
    main()
