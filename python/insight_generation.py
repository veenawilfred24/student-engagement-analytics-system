"""Generate portfolio-ready analytical insights from processed data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INSIGHTS_DIR = ROOT_DIR / "insights"


def load_segmented_data() -> pd.DataFrame:
    path = PROCESSED_DIR / "student_segments.csv"
    if not path.exists():
        raise FileNotFoundError("Run feature_engineering.py and student_segmentation.py first.")
    return pd.read_csv(path)


def build_school_insights(segmented: pd.DataFrame) -> pd.DataFrame:
    return (
        segmented.groupby(["school_id", "school_name", "region", "school_type"], as_index=False)
        .agg(
            students=("student_id", "count"),
            dropout_rate=("dropped_out", "mean"),
            avg_engagement_rate=("engagement_rate", "mean"),
            avg_assessment_score=("avg_assessment_score", "mean"),
            high_risk_students=("risk_score", lambda series: int((series >= 0.62).sum())),
            avg_implementation_quality=("implementation_quality", "mean"),
        )
        .assign(
            engagement_index=lambda frame: (
                frame["avg_engagement_rate"] * 45
                + frame["avg_assessment_score"] / 100 * 30
                + (1 - frame["dropout_rate"]) * 25
            )
        )
        .sort_values("engagement_index", ascending=False)
    )


def write_markdown_report(segmented: pd.DataFrame, school_insights: pd.DataFrame) -> None:
    INSIGHTS_DIR.mkdir(exist_ok=True)
    dropout_rate = segmented["dropped_out"].mean()
    high_risk_rate = (segmented["risk_score"] >= 0.62).mean()
    top_segment = segmented["engagement_segment"].value_counts().idxmax()
    top_school = school_insights.iloc[0]
    bottom_school = school_insights.iloc[-1]
    declining = segmented[segmented["engagement_momentum"] < 0]
    improving = segmented[segmented["engagement_momentum"] > 0]
    poor_internet = segmented[segmented["internet_quality"] == "Poor"]
    good_internet = segmented[segmented["internet_quality"] == "Good"]
    top_quartile_cutoff = school_insights["engagement_index"].quantile(0.75)
    bottom_quartile_cutoff = school_insights["engagement_index"].quantile(0.25)
    top_quartile = school_insights[school_insights["engagement_index"] >= top_quartile_cutoff]
    bottom_quartile = school_insights[school_insights["engagement_index"] <= bottom_quartile_cutoff]
    segment_summary = (
        segmented.groupby("engagement_segment", observed=True)
        .agg(
            students=("student_id", "count"),
            dropout_rate=("dropped_out", "mean"),
            avg_engagement_rate=("engagement_rate", "mean"),
            avg_score=("avg_assessment_score", "mean"),
        )
        .sort_values("students", ascending=False)
    )

    markdown = f"""# Key Findings

## Executive Summary

This anonymized case study analyzes {len(segmented):,} synthetic learners across {school_insights['school_id'].nunique():,} schools. The dataset is not intended to represent a real employer's student population; it is a reproducible proxy built to demonstrate how engagement, retention, and school-support analytics can be structured.

The modeled term dropout rate is {dropout_rate:.1%}. The current risk rules flag {high_risk_rate:.1%} of learners for high-priority review.

## Findings

1. **Recent engagement trend is the clearest intervention signal.** Learners with declining momentum have a {declining['dropped_out'].mean():.1%} dropout rate, compared with {improving['dropped_out'].mean():.1%} for learners with improving momentum.
2. **Connectivity is a practical support constraint.** Learners marked with poor internet quality show a {poor_internet['dropped_out'].mean():.1%} dropout rate, compared with {good_internet['dropped_out'].mean():.1%} for learners with good internet quality.
3. **School outcomes vary enough to justify a ranking workflow.** Top-quartile schools average a {top_quartile['dropout_rate'].mean():.1%} dropout rate and {top_quartile['avg_engagement_rate'].mean():.1%} active-day rate. Bottom-quartile schools average a {bottom_quartile['dropout_rate'].mean():.1%} dropout rate and {bottom_quartile['avg_engagement_rate'].mean():.1%} active-day rate.
4. **The largest operating segment is `{top_segment}`.** That group contains {segment_summary.loc[top_segment, 'students']:,} learners and has a {segment_summary.loc[top_segment, 'dropout_rate']:.1%} dropout rate.
5. **The school index produces interpretable extremes.** `{top_school['school_name']}` leads with an engagement index of {top_school['engagement_index']:.1f}; `{bottom_school['school_name']}` trails at {bottom_school['engagement_index']:.1f}.

## Recommendations

1. Create a weekly intervention list for students with negative engagement momentum, 14+ inactive days, or risk score above 0.62.
2. Separate outreach into two queues: re-engagement for inactive learners and academic support for active learners with low pass rates.
3. Use the bottom-quartile school list for school-success coaching, not punitive performance management.
4. Track active-day rate and final-month retention as primary dashboard KPIs; treat raw login/session counts as diagnostic metrics.
5. Review risk outcomes by connectivity and socioeconomic bands before using the queue in any real operational setting.

## Caveats

- All data is synthetic and should be interpreted as a case-study simulation.
- Risk scoring is rule-based for explainability; it is not a validated predictive model.
- Sensitive attributes are included only to demonstrate support-equity analysis and would require governance review in production.
"""
    (INSIGHTS_DIR / "key_findings.md").write_text(markdown, encoding="utf-8")


def main() -> None:
    segmented = load_segmented_data()
    school_insights = build_school_insights(segmented)
    school_insights.to_csv(PROCESSED_DIR / "school_engagement_rankings.csv", index=False)
    write_markdown_report(segmented, school_insights)
    print("Insight report and school rankings generated.")


if __name__ == "__main__":
    main()
