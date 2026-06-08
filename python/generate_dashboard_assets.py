"""Generate dashboard preview images from processed portfolio data.

The images are saved under dashboard/assets/ and embedded in README.md. They are
static previews of the Power BI dashboard design, not a replacement for the
dashboard specification.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/student-engagement-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/student-engagement-cache")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ASSET_DIR = ROOT_DIR / "dashboard" / "assets"

COLORS = {
    "teal": "#0F766E",
    "teal_dark": "#134E4A",
    "amber": "#D97706",
    "red": "#B91C1C",
    "blue": "#2563EB",
    "gray": "#475569",
    "light_gray": "#E2E8F0",
    "bg": "#F8FAFC",
}


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#CBD5E1",
            "axes.labelcolor": "#334155",
            "xtick.color": "#475569",
            "ytick.color": "#475569",
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.titlesize": 14,
        }
    )


def load_data() -> dict[str, pd.DataFrame]:
    return {
        "students": pd.read_csv(DATA_DIR / "students.csv"),
        "events": pd.read_csv(DATA_DIR / "engagement_events.csv", parse_dates=["event_date"]),
        "features": pd.read_csv(PROCESSED_DIR / "student_features.csv"),
        "segments": pd.read_csv(PROCESSED_DIR / "student_segments.csv"),
        "schools": pd.read_csv(PROCESSED_DIR / "school_engagement_rankings.csv"),
    }


def save(fig: plt.Figure, filename: str) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(ASSET_DIR / filename, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def create_overview_kpis(data: dict[str, pd.DataFrame]) -> None:
    students = data["students"]
    features = data["features"]
    total_students = len(students)
    avg_engagement = features["engagement_rate"].mean()
    retention_rate = 1 - students["dropped_out"].mean()

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
    kpis = [
        ("Total Students", f"{total_students:,}", "Synthetic learner population", COLORS["teal"]),
        ("Avg Engagement", f"{avg_engagement:.1%}", "Mean active-day rate", COLORS["blue"]),
        ("Retention Rate", f"{retention_rate:.1%}", "Students retained through term", COLORS["amber"]),
    ]

    for ax, (title, value, subtitle, color) in zip(axes, kpis):
        ax.set_axis_off()
        ax.add_patch(
            plt.Rectangle(
                (0, 0),
                1,
                1,
                transform=ax.transAxes,
                facecolor=COLORS["bg"],
                edgecolor=COLORS["light_gray"],
                linewidth=1.4,
            )
        )
        ax.text(0.07, 0.78, title, transform=ax.transAxes, color=COLORS["gray"], fontsize=11, weight="bold")
        ax.text(0.07, 0.43, value, transform=ax.transAxes, color=color, fontsize=28, weight="bold")
        ax.text(0.07, 0.18, subtitle, transform=ax.transAxes, color=COLORS["gray"], fontsize=9)

    fig.suptitle("Student Engagement Overview", x=0.03, ha="left", y=1.08, fontsize=16, weight="bold")
    save(fig, "overview_kpis.png")


def create_engagement_trends(data: dict[str, pd.DataFrame]) -> None:
    events = data["events"]
    students = data["students"]
    trend = (
        events.groupby("event_date")
        .agg(active_students=("student_id", "nunique"), sessions=("event_id", "count"))
        .reset_index()
        .sort_values("event_date")
    )
    trend["active_rate"] = trend["active_students"] / len(students)
    trend["rolling_active_rate"] = trend["active_rate"].rolling(7, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(trend["event_date"], trend["active_rate"], color="#94A3B8", linewidth=1, alpha=0.65, label="Daily active rate")
    ax.plot(trend["event_date"], trend["rolling_active_rate"], color=COLORS["teal"], linewidth=2.8, label="7-day rolling rate")
    ax.set_title("Engagement Trend Across the Term", loc="left")
    ax.set_ylabel("Active student rate")
    ax.set_xlabel("")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    ax.grid(axis="y", color=COLORS["light_gray"], linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    save(fig, "engagement_trends.png")


def create_school_comparison(data: dict[str, pd.DataFrame]) -> None:
    schools = data["schools"].copy()
    top = schools.nlargest(5, "engagement_index")
    bottom = schools.nsmallest(5, "engagement_index")
    comparison = pd.concat([top, bottom]).sort_values("engagement_index")
    colors = [COLORS["red"] if row in bottom["school_id"].tolist() else COLORS["teal"] for row in comparison["school_id"]]

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.barh(comparison["school_name"], comparison["engagement_index"], color=colors)
    ax.set_title("Top and Bottom Schools by Engagement Index", loc="left")
    ax.set_xlabel("Engagement index")
    ax.grid(axis="x", color=COLORS["light_gray"], linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    for index, value in enumerate(comparison["engagement_index"]):
        ax.text(value + 0.8, index, f"{value:.1f}", va="center", color=COLORS["gray"], fontsize=9)
    ax.set_xlim(0, max(comparison["engagement_index"]) + 12)
    save(fig, "school_comparison.png")


def create_dropoff_funnel(data: dict[str, pd.DataFrame]) -> None:
    students = data["students"]
    events = data["events"]
    activity = events.groupby("student_id").agg(
        active_days=("event_date", "nunique"),
        sessions=("event_id", "count"),
        lesson_views=("activity_type", lambda series: (series == "lesson_view").sum()),
        quiz_attempts=("activity_type", lambda series: (series == "quiz_attempt").sum()),
        assignment_submits=("activity_type", lambda series: (series == "assignment_submit").sum()),
    )
    base = students[["student_id", "dropped_out"]].join(activity, on="student_id").fillna(0)
    stages = pd.Series(
        {
            "Enrolled": len(base),
            "Activated": (base["sessions"] >= 1).sum(),
            "3+ Active Days": (base["active_days"] >= 3).sum(),
            "5+ Lessons": (base["lesson_views"] >= 5).sum(),
            "3+ Quizzes": (base["quiz_attempts"] >= 3).sum(),
            "Submitted Assignment": (base["assignment_submits"] >= 1).sum(),
            "Retained": ((base["active_days"] >= 21) & (~base["dropped_out"].astype(bool))).sum(),
        }
    )

    fig, ax = plt.subplots(figsize=(12, 4.8))
    y = np.arange(len(stages))
    widths = stages.values
    left = (stages.iloc[0] - widths) / 2
    colors = ["#0F766E", "#14877E", "#2A9D8F", "#E0A52B", "#D97706", "#C65D17", "#B91C1C"]
    ax.barh(y, widths, left=left, color=colors, edgecolor="white", height=0.68)
    ax.set_yticks(y, stages.index)
    ax.invert_yaxis()
    ax.set_title("Learner Drop-off Funnel", loc="left")
    ax.set_xlabel("Students")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color=COLORS["light_gray"], linewidth=0.8)
    for idx, value in enumerate(widths):
        ax.text(left[idx] + value / 2, idx, f"{value:,}\n{value / stages.iloc[0]:.0%}", ha="center", va="center", color="white", weight="bold", fontsize=9)
    save(fig, "dropoff_funnel.png")


def create_accuracy_vs_attempts(data: dict[str, pd.DataFrame]) -> None:
    events = data["events"]
    students = data["students"][["student_id", "grade"]]
    scatter = (
        events.groupby("student_id")
        .agg(attempted_questions=("attempted_questions", "sum"), accuracy_rate=("accuracy_rate", "mean"))
        .join(students.set_index("student_id"), on="student_id")
        .sample(n=1200, random_state=42)
    )

    fig, ax = plt.subplots(figsize=(11, 5.2))
    points = ax.scatter(
        scatter["attempted_questions"],
        scatter["accuracy_rate"],
        c=scatter["grade"],
        cmap="viridis",
        alpha=0.62,
        s=24,
        edgecolors="none",
    )
    ax.set_title("Accuracy vs Attempt Volume", loc="left")
    ax.set_xlabel("Attempted questions per student")
    ax.set_ylabel("Average accuracy")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    ax.grid(color=COLORS["light_gray"], linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    cbar = fig.colorbar(points, ax=ax, pad=0.01)
    cbar.set_label("Grade")
    save(fig, "accuracy_vs_attempts.png")


def main() -> None:
    configure_style()
    data = load_data()
    create_overview_kpis(data)
    create_engagement_trends(data)
    create_school_comparison(data)
    create_dropoff_funnel(data)
    create_accuracy_vs_attempts(data)
    print(f"Dashboard assets saved to {ASSET_DIR}")


if __name__ == "__main__":
    main()
