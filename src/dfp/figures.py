"""Static analysis figure for the README, drawn from data/bi/ba_metric_summary.csv.

Usage: python -m dfp.figures   (requires the optional 'figures' extra: matplotlib)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "figures" / "wape_published_vs_corrected.png"

SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e7e6e2"
PUBLISHED, CORRECTED = "#86b6ef", "#184f95"   # one hue, validated ordinal pair
FLAG = "#8a5a00"
GROUPS = [
    ("A", "Systematic and correctable"),
    ("B", "Apparently correctable — source semantics uncertain"),
    ("C", "Persistent bias — low correction benefit"),
    ("D", "Little/no correctable bias"),
]


def draw(summary: pd.DataFrame, out: Path = OUT) -> Path:
    s = summary.copy()
    s["cat"] = s["category"].str[0]
    rows = []                       # (kind, payload) from top to bottom
    for code, label in GROUPS:
        g = s[s["cat"] == code].sort_values("published_wape_pct_common", ascending=False)
        if g.empty:
            continue
        rows.append(("header", f"{code}. {label}"))
        rows.extend(("ba", r) for _, r in g.iterrows())

    fig, ax = plt.subplots(figsize=(10, 6.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    xmax = s["published_wape_pct_common"].max() * 1.02
    n = len(rows)
    for i, (kind, item) in enumerate(rows):
        y = n - i
        if kind == "header":
            ax.text(0, y, item, fontsize=9.5, fontweight="bold", color=INK, va="center")
            continue
        pub, cor = item["published_wape_pct_common"], item["corrected_wape_pct_common"]
        ax.plot([pub, cor], [y, y], color=GRID, linewidth=2.5, solid_capstyle="round", zorder=1)
        ax.scatter([pub], [y], s=70, color=PUBLISHED, edgecolor=SURFACE, linewidth=2, zorder=3)
        ax.scatter([cor], [y], s=70, color=CORRECTED, edgecolor=SURFACE, linewidth=2, zorder=3)
        ax.text(-0.25, y, item["ba_code"], ha="right", va="center", fontsize=10, color=INK)
        label = (f"{pub:.2f}% → {cor:.2f}%   "
                 f"{item['corrected_vs_published_common_delta_pp']:+.2f} pp "
                 f"({item['corrected_vs_published_common_relative_delta_pct']:+.1f}%)").replace("-", "−")
        ax.text(xmax + 0.3, y, label, va="center", fontsize=9, color=INK_2)
        if item["source_semantic_flag"]:
            ax.text(xmax + 0.3, y - 0.36, "SOURCE SEMANTICS UNCERTAIN", va="center", fontsize=7, color=FLAG,
                    fontweight="bold")

    ax.set_ylim(0.3, n + 0.7)
    ax.set_xlim(-0.2, xmax)
    ax.set_yticks([])
    ax.set_xlabel("WAPE, % (common comparison hours)", color=INK_2, fontsize=9)
    ax.tick_params(axis="x", colors=INK_2, labelsize=8.5)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    fig.text(0.02, 0.965, "Published vs bias-corrected WAPE by balancing authority", fontsize=13,
             fontweight="bold", color=INK)
    fig.text(0.02, 0.93, "Sep 2023 – Aug 2026, hourly. Trailing 28-day causal correction; "
             "both forecasts scored on identical hours.", fontsize=9, color=INK_2)
    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=8, color=PUBLISHED, label="Published forecast"),
               plt.Line2D([], [], marker="o", linestyle="", markersize=8, color=CORRECTED, label="Bias-corrected")]
    fig.legend(handles=handles, loc="lower right", bbox_to_anchor=(0.62, 0.885), frameon=False, fontsize=9,
               labelcolor=INK, ncol=2)
    fig.text(0.02, 0.012, "Python analysis figure generated from data/bi/ba_metric_summary.csv. "
             "Change = corrected − published (pp and relative).", fontsize=7.5, color=INK_2)
    fig.subplots_adjust(left=0.07, right=0.62, top=0.89, bottom=0.1)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


if __name__ == "__main__":
    summary = pd.read_csv(ROOT / "data" / "bi" / "ba_metric_summary.csv")
    print(draw(summary))
