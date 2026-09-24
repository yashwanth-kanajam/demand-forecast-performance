"""Analytical layer: benchmarks, segment metrics, correctability, exceptions, reconciliation.

Definitions and thresholds: docs/metric_catalogue.md and config/pipeline.toml.
Sign conventions:
- error e = forecast - actual; positive = overforecast (all bias metrics).
- residual r = actual - forecast; the trailing adjustment is mean(r) and is ADDED
  to the published forecast (see benchmarks.trailing_bias_correction).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .benchmarks import naive_utc_lag, seasonal_naive, trailing_bias_correction
from .config import Config
from .metrics import (
    aggregate,
    derived,
    gaussian_worst_share,
    worst_share,
)

SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}
SEASON_START = {"Winter": 12, "Spring": 3, "Summer": 6, "Autumn": 9}

# segment_type -> column in the enriched table
SEGMENTS = {
    "overall": "_all",
    "eval_year": "eval_year",
    "ref_hour": "ref_hour",
    "day_type": "day_type",
    "ref_month": "ref_month",
    "year_month": "year_month",
    "season": "season",
    "season_period": "season_period",
    "demand_band": "demand_band",
    "high_demand": "high_demand",
    "high_forecast": "high_forecast",
}
FORECASTS = {"published": "forecast_mw", "seasonal_naive": "naive_forecast_mw",
             "bias_corrected": "corrected_forecast_mw"}


# --- enrichment ----------------------------------------------------------------

def enrich(hourly: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    a = cfg.analysis
    h = hourly.copy()
    h = h.join(seasonal_naive(h, a["naive_lag_days"]))
    h["naive_168h_mw"] = naive_utc_lag(h, 168)
    h = h.join(trailing_bias_correction(h, a["correction_window_days"], a["correction_gap_days"],
                                        a["correction_min_days"]))
    h["error_mw"] = (h["forecast_mw"] - h["actual_mw"]).where(h["is_paired"])
    h["abs_error_mw"] = h["error_mw"].abs()
    h["in_common_set"] = h["is_paired"] & h["naive_forecast_mw"].notna() & h["corrected_forecast_mw"].notna()

    d = h["ref_date"]
    start = pd.Timestamp(cfg.start_ref_date)
    months_in = (d.dt.year - start.year) * 12 + d.dt.month - start.month
    h["eval_year"] = "Y" + (months_in // 12 + 1).astype(str)
    h["ref_month"] = d.dt.month
    h["year_month"] = d.dt.strftime("%Y-%m")
    h["season"] = d.dt.month.map(SEASONS)
    season_year = np.where(d.dt.month == 12, d.dt.year, np.where(d.dt.month <= 2, d.dt.year - 1, d.dt.year))
    h["season_period"] = (pd.Series(season_year, index=h.index).astype(str) + "-"
                          + h["season"].map(SEASON_START).map("{:02d}".format) + " " + h["season"])
    h["day_type"] = np.where(d.dt.dayofweek >= 5, "weekend", "weekday")
    h["_all"] = "all"

    q = a["high_demand_quantile"]
    paired = h[h["is_paired"]]
    act_q = paired.groupby("ba_code")["actual_mw"].quantile(q)
    fc_q = paired.groupby("ba_code")["forecast_mw"].quantile(q)
    h["high_demand"] = np.where(~h["is_paired"], None,
                                np.where(h["actual_mw"] >= h["ba_code"].map(act_q), "high", "other"))
    h["high_forecast"] = np.where(~h["is_paired"], None,
                                  np.where(h["forecast_mw"] >= h["ba_code"].map(fc_q), "high", "other"))
    labels = [f"Q{i}" for i in range(1, a["demand_bands"] + 1)]
    h["demand_band"] = None
    for ba, rows in paired.groupby("ba_code"):
        h.loc[rows.index, "demand_band"] = pd.qcut(rows["actual_mw"], a["demand_bands"], labels=labels).astype(str)
    return h


# --- segment metrics -----------------------------------------------------------

def segment_metrics(h: pd.DataFrame) -> pd.DataFrame:
    """Long table: BA x segment x evaluation set x forecast type."""
    out = []
    common = h[h["in_common_set"]]
    for seg_type, col in SEGMENTS.items():
        jobs = [("paired", h, "published")] + [("common", common, f) for f in FORECASTS]
        for eval_set, data, ftype in jobs:
            g = aggregate(data, ["ba_code", col], "actual_mw", FORECASTS[ftype])
            g = g.rename(columns={col: "segment_value"})
            g.insert(1, "segment_type", seg_type)
            g.insert(3, "eval_set", eval_set)
            g.insert(4, "forecast_type", ftype)
            out.append(g)
    seg = pd.concat(out, ignore_index=True)
    seg["segment_value"] = seg["segment_value"].astype(str)
    return seg


def tail_metrics(h: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Worst-1% contribution, published forecast, paired set, whole window and by evaluation year."""
    rows = []
    share = cfg.analysis["worst_share"]
    for (ba, period), g in pd.concat([h.assign(period="all"), h.assign(period=h["eval_year"])]) \
            .loc[lambda x: x["is_paired"]].groupby(["ba_code", "period"]):
        rows.append({"ba_code": ba, "period": period, "n_hours": len(g),
                     "worst1_contribution_pct": worst_share(g["abs_error_mw"], g["utc_period_end"], share)})
    return pd.DataFrame(rows)


# --- correctability ------------------------------------------------------------

def _rel(corr, pub):
    return 100 * (corr / pub - 1)


def correctability(seg: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    a = cfg.analysis
    mat = 100 * a["project_rule_relative_change"]
    c = seg[seg["eval_set"] == "common"]
    wide = c.pivot_table(index=["ba_code", "segment_type", "segment_value"], columns="forecast_type",
                         values=["wape_pct", "norm_bias_pct", "mae_mw", "sum_abs_error_mw_h", "n_hours"])
    rows = []
    for ba in sorted(c["ba_code"].unique()):
        w = wide.loc[ba]
        ov = w.loc[("overall", "all")]
        years = w.loc["eval_year"]
        quarters = w.loc["season_period"]
        hours = w.loc["ref_hour"]
        rel_all = _rel(ov[("wape_pct", "bias_corrected")], ov[("wape_pct", "published")])
        rel_y = _rel(years[("wape_pct", "bias_corrected")], years[("wape_pct", "published")])
        rel_q = _rel(quarters[("wape_pct", "bias_corrected")], quarters[("wape_pct", "published")])
        rel_h = _rel(hours[("wape_pct", "bias_corrected")], hours[("wape_pct", "published")])
        hd = w.loc[("high_demand", "high")]
        reduction_h = hours[("sum_abs_error_mw_h", "published")] - hours[("sum_abs_error_mw_h", "bias_corrected")]
        total_red = reduction_h.sum()
        top3 = reduction_h.sort_values(ascending=False).head(3).sum()
        skill = 1 - ov[("wape_pct", "published")] / ov[("wape_pct", "seasonal_naive")]
        skill_y = 1 - years[("wape_pct", "published")] / years[("wape_pct", "seasonal_naive")]

        # Project-defined practical-improvement rule (not an industry materiality threshold).
        if rel_all <= -mat and (rel_y < 0).all():
            cls = "improvement: project rule met"
        elif rel_all >= mat and (rel_y > 0).all():
            cls = "degradation: project rule met"
        elif abs(rel_all) >= mat:
            cls = "mixed across years"
        else:
            cls = "below project rule (|change| < 5%)"
        rows.append({
            "ba_code": ba,
            "common_n_hours": int(ov[("n_hours", "published")]),
            "naive_wape_pct": ov[("wape_pct", "seasonal_naive")],
            "published_wape_pct": ov[("wape_pct", "published")],
            "corrected_wape_pct": ov[("wape_pct", "bias_corrected")],
            "published_mae_mw": ov[("mae_mw", "published")],
            "corrected_mae_mw": ov[("mae_mw", "bias_corrected")],
            "published_norm_bias_pct": ov[("norm_bias_pct", "published")],
            "corrected_norm_bias_pct": ov[("norm_bias_pct", "bias_corrected")],
            "rel_wape_change_pct": rel_all,
            **{f"rel_wape_change_{y}_pct": v for y, v in rel_y.items()},
            "years_improved": int((rel_y < 0).sum()),
            "quarters_improved": int((rel_q < 0).sum()),
            "quarters": int(rel_q.notna().sum()),
            "worst_quarter_rel_change_pct": rel_q.max(),
            "best_quarter_rel_change_pct": rel_q.min(),
            "hours_improved_of_24": int((rel_h < 0).sum()),
            "top3_hours_share_of_error_reduction_pct": 100 * top3 / total_red if total_red > 0 else np.nan,
            "high_demand_rel_wape_change_pct": _rel(hd[("wape_pct", "bias_corrected")], hd[("wape_pct", "published")]),
            "high_demand_published_norm_bias_pct": hd[("norm_bias_pct", "published")],
            "high_demand_corrected_norm_bias_pct": hd[("norm_bias_pct", "bias_corrected")],
            "project_rule_class": cls,
            "skill_vs_naive": skill,
            "years_published_beats_naive": int((skill_y > 0).sum()),
            "published_beats_naive_project_rule": bool(skill >= a["naive_skill_project_rule"] and (skill_y > 0).all()),
        })
    return pd.DataFrame(rows)


def naive_dst_sensitivity(h: pd.DataFrame) -> pd.DataFrame:
    """Primary reference-clock naive vs strict 168-hour UTC lag, on common-set hours where both exist."""
    rows = []
    for ba, g in h[h["in_common_set"] & h["naive_168h_mw"].notna()].groupby("ba_code"):
        differs = (g["naive_forecast_mw"] != g["naive_168h_mw"])
        prim = derived(len(g), g["actual_mw"].sum(), (g["naive_forecast_mw"] - g["actual_mw"]).abs().sum(), 0)
        alt = derived(len(g), g["actual_mw"].sum(), (g["naive_168h_mw"] - g["actual_mw"]).abs().sum(), 0)
        rows.append({"ba_code": ba, "n_hours": len(g), "hours_definitions_differ": int(differs.sum()),
                     "naive_ref_clock_wape_pct": prim["wape_pct"], "naive_168h_wape_pct": alt["wape_pct"]})
    return pd.DataFrame(rows)


def benchmark_coverage(h: pd.DataFrame) -> pd.DataFrame:
    """Per BA: seasonal-naive lookup outcomes and correction availability over all grid hours."""
    status = pd.crosstab(h["ba_code"], h["naive_status"]).add_prefix("naive_")
    g = h.groupby("ba_code")
    out = pd.DataFrame({
        "grid_hours": g.size(),
        "paired_hours": g["is_paired"].sum(),
        "paired_with_naive": (h["is_paired"] & h["naive_forecast_mw"].notna()).groupby(h["ba_code"]).sum(),
        "paired_with_correction": (h["is_paired"] & h["corrected_forecast_mw"].notna()).groupby(h["ba_code"]).sum(),
        "common_set_hours": g["in_common_set"].sum(),
    })
    return out.join(status).reset_index()


def correction_by_period(seg: pd.DataFrame) -> pd.DataFrame:
    """Common-set WAPE, published vs corrected, by BA x evaluation year and BA x quarter (season-year)."""
    c = seg[(seg["eval_set"] == "common") & seg["segment_type"].isin(["eval_year", "season_period"])
            & seg["forecast_type"].isin(["published", "bias_corrected"])]
    w = c.pivot_table(index=["ba_code", "segment_type", "segment_value"], columns="forecast_type",
                      values=["wape_pct", "n_hours"]).reset_index()
    w.columns = ["ba_code", "period_type", "period", "n_hours", "_n2", "corrected_wape_pct", "published_wape_pct"]
    w = w.drop(columns="_n2")
    w["rel_wape_change_pct"] = _rel(w["corrected_wape_pct"], w["published_wape_pct"])
    w["period_type"] = w["period_type"].map({"eval_year": "year", "season_period": "quarter"})
    w["n_hours"] = w["n_hours"].astype(int)
    return w[["ba_code", "period_type", "period", "n_hours", "published_wape_pct", "corrected_wape_pct",
              "rel_wape_change_pct"]].sort_values(["ba_code", "period_type", "period"], ignore_index=True)


# --- exceptions ----------------------------------------------------------------

def extreme_concentration_threshold_pct(cfg: Config) -> float:
    """Worst-1% contribution (in percent) at or above which EXTREME_HOUR_CONCENTRATION fires."""
    return cfg.exceptions["extreme_concentration_multiple"] * 100 * gaussian_worst_share(cfg.analysis["worst_share"])


EXCEPTION_RULES = {
    "PERSISTENT_DIRECTIONAL_BIAS": "|normalized bias| >= {persistent_bias_pct}% (paired set) and same sign in every evaluation year",
    "HOUR_SPECIFIC_BIAS": ">= {hour_bias_min_hours} reference hours with |normalized bias| >= {hour_bias_pct}% and same sign in every evaluation year",
    "HIGH_DEMAND_UNDERFORECAST": "high-demand normalized bias <= -{high_demand_bias_pct}% in every evaluation year on both actual-defined and forecast-defined top-decile hours",
    "HIGH_DEMAND_OVERFORECAST": "high-demand normalized bias >= +{high_demand_bias_pct}% in every evaluation year on both actual-defined and forecast-defined top-decile hours",
    "EXTREME_HOUR_CONCENTRATION": "worst-1% contribution >= {extreme_concentration_multiple} x Gaussian reference",
    "SEASON_SPECIFIC_DETERIORATION": "a season's WAPE >= {season_deterioration_ratio} x BA overall WAPE in every season-year observed (at least 2)",
    "PRACTICAL_GAIN_FROM_CORRECTION": "project-defined practical-improvement rule: common-set WAPE change <= -5% overall and lower in every evaluation year",
    "CORRECTION_DEGRADES_FORECAST": "project-defined rule: common-set WAPE change >= +5% overall and higher in every evaluation year",
    "ERROR_NOT_BIAS_CORRECTABLE": "correction below the project rule (|change| < 5%) or degrades, and |normalized bias| < {persistent_bias_pct}%",
    "SOURCE_SEMANTIC_FORECAST_LEVEL_ANOMALY": "flagged by the source-semantics audit (docs/source_semantics_audit.md); correction is real in the reported series but its meaning is undetermined",
    "WEAK_SKILL_VS_NAIVE": "published forecast does not beat seasonal naive by skill >= 0.20 overall and in every evaluation year",
}


def exceptions(seg: pd.DataFrame, tails: pd.DataFrame, corr: pd.DataFrame, cross: dict,
               cfg: Config) -> pd.DataFrame:
    x = cfg.exceptions
    p = seg[(seg["eval_set"] == "paired") & (seg["forecast_type"] == "published")]
    worst_ref = extreme_concentration_threshold_pct(cfg)
    out = []

    def flag(ba, code, evidence, n_hours):
        out.append({"ba_code": ba, "exception": code, "evidence": evidence, "n_hours": int(n_hours),
                    "rule": EXCEPTION_RULES[code].format(**x)})

    n_years = p[p["segment_type"] == "eval_year"]["segment_value"].nunique()
    for ba in sorted(p["ba_code"].unique()):
        b = p[p["ba_code"] == ba]
        seg_ = lambda t: b[b["segment_type"] == t].set_index("segment_value")
        ov, yrs = seg_("overall").loc["all"], seg_("eval_year")
        nb, nb_y = ov["norm_bias_pct"], yrs["norm_bias_pct"]

        if abs(nb) >= x["persistent_bias_pct"] and (np.sign(nb_y) == np.sign(nb)).all():
            flag(ba, "PERSISTENT_DIRECTIONAL_BIAS",
                 f"normalized bias {nb:+.2f}% (n={int(ov['n_hours'])}); by year "
                 + ", ".join(f"{k} {v:+.2f}%" for k, v in nb_y.items()), ov["n_hours"])

        hy = cross["hour_year"][cross["hour_year"]["ba_code"] == ba]
        hits = []
        for hr, g in hy.groupby("ref_hour"):
            s = np.sign(g["norm_bias_pct"])
            if (g["norm_bias_pct"].abs() >= x["hour_bias_pct"]).all() and (s == s.iloc[0]).all():
                hits.append((hr, g["norm_bias_pct"].mean()))
        if len(hits) >= x["hour_bias_min_hours"]:
            flag(ba, "HOUR_SPECIFIC_BIAS",
                 f"{len(hits)} reference hours with |normalized bias| >= {x['hour_bias_pct']}% and same sign in every year: "
                 + ", ".join(f"h{int(hr):02d} ({v:+.1f}%)" for hr, v in hits),
                 hy[hy["ref_hour"].isin([h_ for h_, _ in hits])]["n_hours"].sum())

        for kind in ("under", "over"):
            sign = -1 if kind == "under" else 1
            ok_all = True
            ev = []
            n_hd = 0
            for col in ("high_demand", "high_forecast"):
                ct = cross[col]
                yb = ct[(ct["ba_code"] == ba) & (ct["segment"] == "high")].set_index("eval_year")["norm_bias_pct"]
                ev.append(f"{col}: " + ", ".join(f"{k} {v:+.2f}%" for k, v in yb.items()))
                if col == "high_demand":
                    n_hd = ct[(ct["ba_code"] == ba) & (ct["segment"] == "high")]["n_hours"].sum()
                ok_all &= bool((sign * yb >= x["high_demand_bias_pct"]).all()) and len(yb) == n_years
            if ok_all:
                flag(ba, f"HIGH_DEMAND_{kind.upper()}FORECAST", "; ".join(ev), n_hd)

        t = tails[(tails["ba_code"] == ba) & (tails["period"] == "all")].iloc[0]
        if t["worst1_contribution_pct"] >= worst_ref:
            flag(ba, "EXTREME_HOUR_CONCENTRATION",
                 f"worst 1% of hours carry {t['worst1_contribution_pct']:.1f}% of absolute error "
                 f"(Gaussian reference {worst_ref / x['extreme_concentration_multiple']:.2f}%)", t["n_hours"])

        sp = seg_("season_period")
        for season in SEASON_START:
            s = sp[sp.index.str.endswith(season)]
            ratio = s["wape_pct"] / ov["wape_pct"]
            if len(s) >= 2 and (ratio >= x["season_deterioration_ratio"]).all():
                flag(ba, "SEASON_SPECIFIC_DETERIORATION",
                     f"{season} WAPE / overall WAPE by season-year: "
                     + ", ".join(f"{i.split(' ')[0]} {r:.2f}x" for i, r in ratio.items()), s["n_hours"].sum())

        c = corr[corr["ba_code"] == ba].iloc[0]
        year_cols = sorted(k for k in c.index if k.startswith("rel_wape_change_Y"))
        rel = f"relative WAPE change {c['rel_wape_change_pct']:+.1f}% (years " + ", ".join(
            f"{c[k]:+.1f}%" for k in year_cols) + ")"
        n_c = c["common_n_hours"]
        if c["project_rule_class"] == "improvement: project rule met":
            flag(ba, "PRACTICAL_GAIN_FROM_CORRECTION", rel, n_c)
        if c["project_rule_class"] == "degradation: project rule met":
            flag(ba, "CORRECTION_DEGRADES_FORECAST", rel, n_c)
        if (c["project_rule_class"] in ("below project rule (|change| < 5%)", "degradation: project rule met")
                and abs(nb) < x["persistent_bias_pct"]):
            flag(ba, "ERROR_NOT_BIAS_CORRECTABLE", f"normalized bias {nb:+.2f}%; {rel}", n_c)
        if ba in cfg.source_flagged_bas:
            flag(ba, "SOURCE_SEMANTIC_FORECAST_LEVEL_ANOMALY",
                 f"normalized bias {nb:+.2f}%; see docs/source_semantics_audit.md", ov["n_hours"])
        if not c["published_beats_naive_project_rule"]:
            flag(ba, "WEAK_SKILL_VS_NAIVE",
                 f"skill {c['skill_vs_naive']:.2f}; published better than naive in {c['years_published_beats_naive']}/3 years", n_c)
    return pd.DataFrame(out, columns=["ba_code", "exception", "evidence", "n_hours", "rule"])


def cross_tables(h: pd.DataFrame) -> dict:
    """BA x hour x year and BA x high-demand x year tables used by the exception rules."""
    paired = h[h["is_paired"]]
    out = {"hour_year": aggregate(paired, ["ba_code", "ref_hour", "eval_year"], "actual_mw", "forecast_mw")}
    for col in ("high_demand", "high_forecast"):
        out[col] = aggregate(paired, ["ba_code", col, "eval_year"], "actual_mw", "forecast_mw") \
            .rename(columns={col: "segment"})
    return out


# --- reconciliation ------------------------------------------------------------

def peak_robustness(seg: pd.DataFrame, cross: dict, cfg: Config) -> pd.DataFrame:
    """Peak (top-decile) bias under the actual-defined and forecast-defined selections.

    Only a pattern that survives both selections is 'robust'. Actual-defined only is
    'selection-sensitive' (retrospective diagnostic, never an exception).
    """
    thr = cfg.exceptions["high_demand_bias_pct"]
    p = seg[(seg["eval_set"] == "paired") & (seg["forecast_type"] == "published") & (seg["segment_value"] == "high")]
    rows = []
    for ba in sorted(p["ba_code"].unique()):
        rec = {"ba_code": ba}
        met = {}
        for col, label in (("high_demand", "actual_defined"), ("high_forecast", "forecast_defined")):
            ov = p[(p["ba_code"] == ba) & (p["segment_type"] == col)].iloc[0]
            yb = cross[col][(cross[col]["ba_code"] == ba) & (cross[col]["segment"] == "high")]["norm_bias_pct"]
            rec[f"{label}_n_hours"] = int(ov["n_hours"])
            rec[f"{label}_norm_bias_pct"] = ov["norm_bias_pct"]
            rec[f"{label}_years"] = ", ".join(f"{v:+.2f}" for v in yb)
            n_years = cross[col]["eval_year"].nunique()
            met[label] = ("under" if len(yb) == n_years and (yb <= -thr).all()
                          else "over" if len(yb) == n_years and (yb >= thr).all() else None)
        rec["peak_robustness"] = classify_peak(met["actual_defined"], met["forecast_defined"])
        rows.append(rec)
    return pd.DataFrame(rows)


def classify_peak(actual_dir: str | None, forecast_dir: str | None) -> str:
    if actual_dir and actual_dir == forecast_dir:
        return f"robust {actual_dir}forecast"
    if actual_dir and not forecast_dir:
        return f"selection-sensitive ({actual_dir}forecast on actual-defined peaks only)"
    if forecast_dir and not actual_dir:
        return f"forecast-defined {forecast_dir}forecast only"
    if actual_dir and forecast_dir:
        return "contradictory"
    return "no consistent peak bias"


def assign_category(project_rule_class: str, norm_bias_pct: float, persistent_bias: bool,
                    source_flagged: bool, bias_threshold_pct: float) -> str:
    """Final analytical category (docs/metric_catalogue.md). Returns 'unclassified' if no rule fits."""
    improved = project_rule_class == "improvement: project rule met"
    if improved and source_flagged:
        return "B: apparently correctable, source semantics uncertain"
    if improved:
        return "A: systematic and correctable"
    if persistent_bias:
        return "C: persistent bias, low practical benefit from correction"
    if abs(norm_bias_pct) < bias_threshold_pct:
        return "D: little or no correctable bias"
    return "unclassified"


def reconciliation(seg: pd.DataFrame, tails: pd.DataFrame, corr: pd.DataFrame, exc: pd.DataFrame,
                   peaks: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Reference values Power BI must reproduce.

    *_all_paired: incumbent KPIs on every paired hour.
    *_common: benchmark comparison on the identical common-set hours for all three forecasts.
    """
    def pick(eval_set, ftype, stype="overall", value="all"):
        s = seg[(seg["eval_set"] == eval_set) & (seg["forecast_type"] == ftype)
                & (seg["segment_type"] == stype) & (seg["segment_value"] == value)]
        return s.set_index("ba_code")

    pa, pc = pick("paired", "published"), pick("common", "published")
    nc, cc = pick("common", "seasonal_naive"), pick("common", "bias_corrected")
    hd = pick("paired", "published", "high_demand", "high")
    t = tails[tails["period"] == "all"].set_index("ba_code")
    c = corr.set_index("ba_code")
    pk = peaks.set_index("ba_code")
    out = pd.DataFrame({
        "paired_n_hours": pa["n_hours"].astype(int),
        "sum_actual_mw_h_all_paired": pa["sum_actual_mw_h"],
        "published_wape_pct_all_paired": pa["wape_pct"],
        "published_mae_mw_all_paired": pa["mae_mw"],
        "published_bias_mw_all_paired": pa["bias_mw"],
        "published_norm_bias_pct_all_paired": pa["norm_bias_pct"],
        "peak_actual_defined_wape_pct_all_paired": hd["wape_pct"],
        "worst1_contribution_pct_all_paired": t["worst1_contribution_pct"],
        "common_n_hours": pc["n_hours"].astype(int),
        "sum_actual_mw_h_common": pc["sum_actual_mw_h"],
        "published_wape_pct_common": pc["wape_pct"],
        "published_mae_mw_common": pc["mae_mw"],
        "published_norm_bias_pct_common": pc["norm_bias_pct"],
        "naive_wape_pct_common": nc["wape_pct"],
        "naive_mae_mw_common": nc["mae_mw"],
        "naive_norm_bias_pct_common": nc["norm_bias_pct"],
        "corrected_wape_pct_common": cc["wape_pct"],
        "corrected_mae_mw_common": cc["mae_mw"],
        "corrected_norm_bias_pct_common": cc["norm_bias_pct"],
        "corrected_vs_published_common_delta_pp": cc["wape_pct"] - pc["wape_pct"],
        "corrected_vs_published_common_relative_delta_pct": 100 * (cc["wape_pct"] / pc["wape_pct"] - 1),
        "published_skill_vs_naive_common": 1 - pc["wape_pct"] / nc["wape_pct"],
        "years_improved_of_3": c["years_improved"],
        "quarters_improved": c["quarters_improved"],
        "quarters_evaluated": c["quarters"],
        "project_rule_class": c["project_rule_class"],
        "peak_robustness": pk["peak_robustness"],
    })
    out["source_semantic_flag"] = out.index.isin(cfg.source_flagged_bas)
    persistent = set(exc.loc[exc["exception"] == "PERSISTENT_DIRECTIONAL_BIAS", "ba_code"])
    out["category"] = [assign_category(out.loc[b, "project_rule_class"], out.loc[b, "published_norm_bias_pct_all_paired"],
                                       b in persistent, bool(out.loc[b, "source_semantic_flag"]),
                                       cfg.exceptions["persistent_bias_pct"]) for b in out.index]
    out["exception_reasons"] = [
        "; ".join(exc.loc[exc["ba_code"] == b, "exception"]) for b in out.index]
    return out.reset_index()


def run(hourly: pd.DataFrame, cfg: Config) -> dict[str, pd.DataFrame]:
    h = enrich(hourly, cfg)
    seg = segment_metrics(h)
    tails = tail_metrics(h, cfg)
    corr = correctability(seg, cfg)
    cross = cross_tables(h)
    exc = exceptions(seg, tails, corr, cross, cfg)
    peaks = peak_robustness(seg, cross, cfg)
    return {
        "hourly": h.drop(columns="_all"),
        "segment_metrics": seg,
        "tail_metrics": tails,
        "correctability": corr,
        "naive_dst_sensitivity": naive_dst_sensitivity(h),
        "benchmark_coverage": benchmark_coverage(h),
        "correction_by_period": correction_by_period(seg),
        "exception_candidates": exc,
        "peak_robustness": peaks,
        "ba_reconciliation": reconciliation(seg, tails, corr, exc, peaks, cfg),
        "reference_values": pd.DataFrame([{
            "gaussian_worst1_share_pct": 100 * gaussian_worst_share(cfg.analysis["worst_share"]),
        }]),
    }
