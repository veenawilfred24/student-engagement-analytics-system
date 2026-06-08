"""Create analytical features for engagement, retention, and risk modeling."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"


def read_best_available(filename: str) -> pd.DataFrame:
    clean_path = PROCESSED_DIR / filename.replace(".csv", "_clean.csv")
    raw_path = DATA_DIR / filename
    path = clean_path if clean_path.exists() else raw_path
    return pd.read_csv(path)


def build_student_features() -> pd.DataFrame:
    students = read_best_available("students.csv")
    schools = read_best_available("schools.csv")
    events = pd.read_csv(PROCESSED_DIR / "events_clean.csv") if (PROCESSED_DIR / "events_clean.csv").exists() else pd.read_csv(DATA_DIR / "engagement_events.csv")
    assessments = read_best_available("assessments.csv")

    events["event_date"] = pd.to_datetime(events["event_date"])
    students["dropped_out"] = students["dropped_out"].astype(bool)

    event_features = events.groupby("student_id").agg(
        active_days=("event_date", "nunique"),
        total_sessions=("event_id", "count"),
        total_minutes=("minutes_spent", "sum"),
        avg_minutes_per_session=("minutes_spent", "mean"),
        total_content_completed=("content_items_completed", "sum"),
        avg_accuracy=("accuracy_rate", "mean"),
        last_active_day=("day_number", "max"),
    )

    recent = events[events["day_number"].between(61, 90)]
    early = events[events["day_number"].between(1, 30)]
    momentum = (
        recent.groupby("student_id")["event_id"].count().rename("recent_sessions").to_frame()
        .join(early.groupby("student_id")["event_id"].count().rename("early_sessions"), how="outer")
        .fillna(0)
    )
    momentum["engagement_momentum"] = momentum["recent_sessions"] - momentum["early_sessions"]

    assessment_features = assessments.groupby("student_id").agg(
        assessments_taken=("assessment_name", "count"),
        avg_assessment_score=("score", "mean"),
        pass_rate=("passed", "mean"),
    )

    features = (
        students.merge(schools, on="school_id", how="left")
        .join(event_features, on="student_id")
        .join(momentum[["recent_sessions", "early_sessions", "engagement_momentum"]], on="student_id")
        .join(assessment_features, on="student_id")
    )

    fill_zero = [
        "active_days",
        "total_sessions",
        "total_minutes",
        "total_content_completed",
        "last_active_day",
        "recent_sessions",
        "early_sessions",
        "engagement_momentum",
        "assessments_taken",
    ]
    features[fill_zero] = features[fill_zero].fillna(0)
    features["avg_minutes_per_session"] = features["avg_minutes_per_session"].fillna(0)
    features["avg_accuracy"] = features["avg_accuracy"].fillna(features["avg_accuracy"].median())
    features["avg_assessment_score"] = features["avg_assessment_score"].fillna(features["avg_assessment_score"].median())
    features["pass_rate"] = features["pass_rate"].fillna(0)

    features["engagement_rate"] = features["active_days"] / 90
    features["minutes_per_active_day"] = np.where(
        features["active_days"] > 0, features["total_minutes"] / features["active_days"], 0
    )
    features["completion_intensity"] = features["total_content_completed"] / 90
    features["inactive_days_since_last_activity"] = 90 - features["last_active_day"]
    features["risk_score"] = (
        (1 - features["engagement_rate"]) * 0.34
        + (features["inactive_days_since_last_activity"] / 90) * 0.22
        + (features["engagement_momentum"].lt(0).astype(int)) * 0.18
        + (1 - features["pass_rate"]) * 0.16
        + (features["internet_quality"].eq("Poor").astype(int)) * 0.10
    ).clip(0, 1)

    output_path = PROCESSED_DIR / "student_features.csv"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_path, index=False)
    return features


def main() -> None:
    features = build_student_features()
    print(f"Student feature table created with {len(features):,} rows.")


if __name__ == "__main__":
    main()
