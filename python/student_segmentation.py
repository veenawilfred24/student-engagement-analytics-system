"""Segment students by engagement behavior using explainable business rules.

The segmentation is intentionally transparent. In production analytics settings,
stakeholders often need clear reasons for intervention categories, not only model
outputs. The rules are kept in code instead of hidden in a dashboard filter so
they can be reviewed, challenged, and adjusted by an operations team.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"


def load_features() -> pd.DataFrame:
    path = PROCESSED_DIR / "student_features.csv"
    if not path.exists():
        raise FileNotFoundError("Run python/feature_engineering.py before segmentation.")
    return pd.read_csv(path)


def assign_segments(features: pd.DataFrame) -> pd.DataFrame:
    segmented = features.copy()
    segmented["engagement_segment"] = "Steady Participants"

    # Engagement thresholds use cohort percentiles instead of fixed activity
    # counts so the rules stay stable if term length or activity volume changes.
    # The 30th percentile creates a reviewable low-engagement queue; the 70th
    # percentile identifies consistently active learners for enrichment.
    high_engagement = segmented["engagement_rate"] >= segmented["engagement_rate"].quantile(0.70)
    low_engagement = segmented["engagement_rate"] <= segmented["engagement_rate"].quantile(0.30)

    # Academic thresholds tie back to the assessment schema: 60 is the pass
    # mark, while 72 is a practical buffer above passing performance.
    strong_performance = segmented["avg_assessment_score"] >= 72
    academic_struggle = segmented["avg_assessment_score"] < 60

    # Negative momentum catches students whose recent usage has fallen below
    # their early-term activity. This is often more actionable than cumulative
    # sessions because it identifies deterioration while there is still time to
    # intervene.
    falling_momentum = segmented["engagement_momentum"] < 0

    # The 0.62 risk threshold creates a high-priority review queue of roughly
    # 10-15% of learners in the synthetic cohort, which is a realistic weekly
    # operating load for a support team.
    high_risk = segmented["risk_score"] >= 0.62

    segmented.loc[high_engagement & strong_performance & ~high_risk, "engagement_segment"] = "High Performers"
    segmented.loc[academic_struggle & ~low_engagement, "engagement_segment"] = "Assessment Strugglers"
    segmented.loc[low_engagement | falling_momentum | high_risk, "engagement_segment"] = "Needs Re-engagement"

    segment_order = pd.CategoricalDtype(
        [
            "Needs Re-engagement",
            "Assessment Strugglers",
            "Steady Participants",
            "High Performers",
        ],
        ordered=True,
    )
    segmented["engagement_segment"] = segmented["engagement_segment"].astype(segment_order)
    return segmented


def summarize_segments(segmented: pd.DataFrame) -> pd.DataFrame:
    return (
        segmented.groupby("engagement_segment", observed=True)
        .agg(
            students=("student_id", "count"),
            dropout_rate=("dropped_out", "mean"),
            avg_engagement_rate=("engagement_rate", "mean"),
            avg_assessment_score=("avg_assessment_score", "mean"),
            avg_risk_score=("risk_score", "mean"),
        )
        .reset_index()
        .sort_values("avg_risk_score", ascending=False)
    )


def main() -> None:
    features = load_features()
    segmented = assign_segments(features)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    segmented.to_csv(PROCESSED_DIR / "student_segments.csv", index=False)
    summarize_segments(segmented).to_csv(PROCESSED_DIR / "segment_summary.csv", index=False)
    print("Student segmentation complete.")


if __name__ == "__main__":
    main()
