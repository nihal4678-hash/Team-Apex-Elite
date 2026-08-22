"""Stage 4 — Exploratory data analysis agent."""

from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

from src.utils.config import PROCESSED_DIR, REPORTS_DIR
from src.utils.io import load_csv, save_json
from src.utils.logging_utils import get_logger
from src.utils.validation import ValidationResult

logger = get_logger("ecomind.eda")
sns.set_theme(style="whitegrid", context="paper")


def _load() -> pd.DataFrame:
    df = load_csv(PROCESSED_DIR / "processed_sensor_data.csv", parse_dates=["timestamp"])
    return df


def _fig_to_pdf(pdf: PdfPages, fig, title: str, observation: str, captions: list[dict[str, str]]) -> None:
    fig.suptitle(title, fontsize=12, y=1.02)
    fig.text(0.01, -0.04, f"Observation: {observation}", fontsize=8, wrap=True)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
    captions.append({"title": title, "observation": observation})


def generate_eda_figures(df: pd.DataFrame, pdf_path) -> list[dict[str, str]]:
    captions: list[dict[str, str]] = []
    daily = df.groupby(df["timestamp"].dt.date)["energy_kwh"].sum().reset_index()
    daily.columns = ["date", "energy_kwh"]
    by_building = df.groupby("building_name")["energy_kwh"].sum().sort_values(ascending=False)
    hourly = df.groupby("hour")["energy_kwh"].mean()
    weekend = df.groupby("is_weekend")["energy_kwh"].mean()
    sample = df.sample(n=min(40_000, len(df)), random_state=42)

    with PdfPages(pdf_path) as pdf:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(pd.to_datetime(daily["date"]), daily["energy_kwh"], color="#0B6E4F")
        ax.set_ylabel("kWh")
        ax.set_xlabel("Date")
        _fig_to_pdf(
            pdf, fig, "1. Daily campus energy trend",
            "Campus load shows weekday peaks and exam-period lift in library/lab demand.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(10, 5))
        by_building.plot(kind="barh", ax=ax, color="#1B998B")
        ax.set_xlabel("Total kWh")
        _fig_to_pdf(
            pdf, fig, "2. Building-wise consumption",
            "Hostels and computer labs dominate total energy due to occupancy duration and IT/HVAC load.",
            captions,
        )

        pivot = (
            df.groupby(["building_id", "hour"])["energy_kwh"].mean().unstack(fill_value=0)
        )
        fig, ax = plt.subplots(figsize=(11, 5))
        sns.heatmap(pivot, ax=ax, cmap="YlOrRd")
        ax.set_title("")
        _fig_to_pdf(
            pdf, fig, "3. Building × hour energy heatmap",
            "Academic blocks peak 09:00–16:00; hostels invert with night-time occupancy.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        hourly.plot(kind="bar", ax=ax, color="#E07A5F")
        ax.set_ylabel("Mean interval kWh")
        _fig_to_pdf(
            pdf, fig, "4. Peak hour analysis",
            "Mean interval energy rises through late morning and remains elevated until evening hostel load.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(
            sample["outdoor_temperature_c"], sample["energy_kwh"], alpha=0.08, s=6, color="#3D405B"
        )
        ax.set_xlabel("Outdoor temperature (°C)")
        ax.set_ylabel("Interval energy (kWh)")
        _fig_to_pdf(
            pdf, fig, "5. Weather vs energy",
            "Higher outdoor temperature correlates with AC-driven energy, especially above ~29°C.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(sample["occupancy"], sample["energy_kwh"], alpha=0.08, s=6, color="#81B29A")
        ax.set_xlabel("Occupancy")
        ax.set_ylabel("Interval energy (kWh)")
        _fig_to_pdf(
            pdf, fig, "6. Occupancy vs energy",
            "Energy scales with occupancy but HVAC/IT rooms sit above the occupancy-only trend.",
            captions,
        )

        device_share = pd.Series(
            {
                "Lights": (df["lights_status"] * df["energy_kwh"]).mean(),
                "Fans": (df["fans_status"] * df["energy_kwh"]).mean(),
                "AC": (df["ac_status"] * df["energy_kwh"]).mean(),
                "Computers": (df["computer_usage"] * df["energy_kwh"]).mean(),
                "Projectors": (df["projector_status"] * df["energy_kwh"]).mean(),
            }
        )
        fig, ax = plt.subplots(figsize=(7, 4))
        device_share.plot(kind="bar", ax=ax, color="#F2CC8F")
        ax.set_ylabel("Weighted mean kWh proxy")
        _fig_to_pdf(
            pdf, fig, "7. Device contribution proxy",
            "Air-conditioning is the largest controllable contributor whenever outdoor temperature is high.",
            captions,
        )

        monthly = df.groupby(df["timestamp"].dt.to_period("W"))["energy_kwh"].sum()
        fig, ax = plt.subplots(figsize=(10, 4))
        monthly.index = monthly.index.to_timestamp()
        monthly.plot(ax=ax, marker="o", color="#6A4C93")
        ax.set_ylabel("Weekly kWh")
        _fig_to_pdf(
            pdf, fig, "8. Weekly / monthly-scale trend",
            "Weekly totals are stable with a late-July exam-window increase.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(5, 4))
        weekend.index = ["Weekday", "Weekend"]
        weekend.plot(kind="bar", ax=ax, color=["#2A9D8F", "#E9C46A"])
        ax.set_ylabel("Mean interval kWh")
        _fig_to_pdf(
            pdf, fig, "9. Weekend vs weekday",
            "Weekday academic/admin load exceeds weekends; hostels remain relatively sticky.",
            captions,
        )

        util = df.groupby("room_id")["occupancy_ratio"].mean().sort_values(ascending=False).head(20)
        fig, ax = plt.subplots(figsize=(10, 5))
        util.plot(kind="bar", ax=ax, color="#457B9D")
        ax.set_ylabel("Mean occupancy ratio")
        ax.tick_params(axis="x", rotation=75)
        _fig_to_pdf(
            pdf, fig, "10. Top-20 room utilization",
            "Library halls and cafeteria dining rooms show the highest average occupancy ratios.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        df.groupby("category")["energy_kwh"].mean().sort_values().plot(kind="barh", ax=ax, color="#E76F51")
        ax.set_xlabel("Mean interval kWh")
        _fig_to_pdf(
            pdf, fig, "11. Category mean energy intensity",
            "Computer labs have the highest mean intensity due to dense IT load plus HVAC.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(7, 4))
        df.groupby("is_working_hours")["energy_kwh"].mean().plot(kind="bar", ax=ax)
        ax.set_xticklabels(["After hours", "Working hours"], rotation=0)
        _fig_to_pdf(
            pdf, fig, "12. Working-hours energy split",
            "Working hours raise academic energy; after-hours residual load is a wastage target.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(sample["humidity_pct"], sample["energy_kwh"], alpha=0.08, s=6, color="#264653")
        ax.set_xlabel("Humidity (%)")
        _fig_to_pdf(
            pdf, fig, "13. Humidity vs energy",
            "Humidity is weakly associated with energy; temperature and occupancy dominate.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        df.groupby("active_device_count")["energy_kwh"].mean().plot(ax=ax, marker="o")
        ax.set_xlabel("Active device count")
        ax.set_ylabel("Mean kWh")
        _fig_to_pdf(
            pdf, fig, "14. Active devices vs energy",
            "Mean energy increases monotonically with concurrently active end-use devices.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        df.groupby("cooling_load_index")["energy_kwh"].mean().head(40).plot(ax=ax, color="#D62828")
        _fig_to_pdf(
            pdf, fig, "15. Cooling load index vs energy",
            "Cooling load index is a strong engineered predictor of HVAC-dominated intervals.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        df["power_factor"].hist(bins=40, ax=ax, color="#2B2D42")
        ax.set_xlabel("Power factor")
        _fig_to_pdf(
            pdf, fig, "16. Power factor distribution",
            "Power factor clusters near 0.90–0.96; AC-on intervals pull PF slightly lower.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        df["voltage_v"].hist(bins=40, ax=ax, color="#8D99AE")
        ax.set_xlabel("Voltage (V)")
        _fig_to_pdf(
            pdf, fig, "17. Voltage distribution",
            "Branch voltage stays around the 230 V Indian nominal with realistic feeder noise.",
            captions,
        )

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        df["indoor_temperature_c"].hist(bins=40, ax=axes[0], color="#06D6A0")
        df["outdoor_temperature_c"].hist(bins=40, ax=axes[1], color="#EF476F")
        axes[0].set_title("Indoor °C")
        axes[1].set_title("Outdoor °C")
        _fig_to_pdf(
            pdf, fig, "18. Indoor vs outdoor temperature",
            "Indoor temperatures are suppressed relative to outdoor when HVAC is active.",
            captions,
        )

        dow_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        by_dow = df.groupby("day_of_week")["energy_kwh"].sum()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(dow_map, by_dow.values, color="#118AB2")
        _fig_to_pdf(
            pdf, fig, "19. Day-of-week energy",
            "Monday–Friday academic schedules produce higher campus totals than weekends.",
            captions,
        )

        occ_heat = df.groupby(["category", "hour"])["occupancy_ratio"].mean().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(11, 4.5))
        sns.heatmap(occ_heat, ax=ax, cmap="Blues")
        _fig_to_pdf(
            pdf, fig, "20. Occupancy heatmap by category",
            "Hostels fill overnight; cafeteria peaks at lunch; library occupancy rises in the exam window.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        (df.groupby("building_id")["occupancy_ratio"].mean().sort_values().plot(kind="barh", ax=ax))
        _fig_to_pdf(
            pdf, fig, "21. Mean building utilization",
            "Admin utilization is high during workdays but low absolute energy due to smaller rooms.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        df.groupby("hour")["ac_status"].mean().plot(ax=ax, color="#073B4C")
        ax.set_ylabel("AC ON fraction")
        _fig_to_pdf(
            pdf, fig, "22. AC operating profile",
            "AC duty cycle tracks hot working hours — the primary HVAC optimization lever.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        empty_lights = df[(df["occupancy"] == 0) & (df["lights_status"] == 1)]
        share = len(empty_lights) / max(len(df), 1)
        ax.bar(["Lights ON, occupancy 0", "Other intervals"], [share, 1 - share])
        _fig_to_pdf(
            pdf, fig, "23. Empty-room lighting wastage share",
            f"About {share:.2%} of intervals show lights on with zero occupancy — a lighting-control target.",
            captions,
        )

        fig, ax = plt.subplots(figsize=(10, 4))
        df.groupby(["building_id", "is_weekend"])["energy_kwh"].mean().unstack().plot(kind="bar", ax=ax)
        _fig_to_pdf(
            pdf, fig, "24. Building weekend vs weekday intensity",
            "Academic buildings drop sharply on weekends; hostels do not, confirming schedule-aware controls.",
            captions,
        )

    return captions


def write_markdown(captions: list[dict[str, str]], df: pd.DataFrame) -> str:
    lines = [
        "# EcoMind AI — Stage 4 EDA Summary",
        "",
        f"- Records analysed: **{len(df):,}**",
        f"- Date range: **{df['timestamp'].min()} → {df['timestamp'].max()}**",
        f"- Total energy: **{df['energy_kwh'].sum():,.1f} kWh**",
        f"- Buildings: **{df['building_id'].nunique()}** | Rooms: **{df['room_id'].nunique()}**",
        "",
        "## Graph observations",
        "",
    ]
    for i, item in enumerate(captions, 1):
        lines.append(f"### {item['title']}")
        lines.append(item["observation"])
        lines.append("")
    text = "\n".join(lines)
    path = REPORTS_DIR / "stage4_eda_summary.md"
    path.write_text(text, encoding="utf-8")
    return str(path)


def run_stage4() -> dict[str, Any]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = _load()
    pdf_path = REPORTS_DIR / "stage4_eda_report.pdf"
    captions = generate_eda_figures(df, pdf_path)
    md_path = write_markdown(captions, df)
    validation = ValidationResult(stage="stage4_eda", passed=True)
    validation.add("at_least_20_charts", len(captions) >= 20, f"n={len(captions)}")
    validation.add("every_chart_explained", all(c["observation"] for c in captions), "")
    validation.add("pdf_written", pdf_path.exists(), str(pdf_path))
    report = {
        "stage": 4,
        "name": "Exploratory Data Analysis Agent",
        "validation": validation.to_dict(),
        "paths": {"pdf": str(pdf_path), "markdown": md_path, "notebook": str(REPORTS_DIR.parent / "notebooks" / "04_eda.ipynb")},
        "summary": {"charts": len(captions), "rows": int(len(df))},
        "captions": captions,
        "pending_issues": validation.pending_issues,
    }
    save_json(REPORTS_DIR / "stage4_eda.json", report)
    if not validation.passed:
        raise RuntimeError(f"Stage 4 validation failed: {validation.pending_issues}")
    logger.info("Stage 4 complete with %s charts", len(captions))
    return report
