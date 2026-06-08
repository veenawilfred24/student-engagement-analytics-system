"""Run lightweight data quality checks for the portfolio dataset.

These checks are intentionally simple and reviewer-friendly. They confirm the
synthetic data matches the case-study contract before downstream analysis is
trusted.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    schools = pd.read_csv(DATA_DIR / "schools.csv")
    students = pd.read_csv(DATA_DIR / "students.csv")
    events = pd.read_csv(DATA_DIR / "engagement_events.csv")
    assessments = pd.read_csv(DATA_DIR / "assessments.csv")

    assert_condition(len(students) == 5_000, "Expected exactly 5,000 students.")
    assert_condition(len(schools) == 100, "Expected exactly 100 schools.")
    assert_condition(students["school_id"].nunique() == 100, "Every school should have assigned students.")
    assert_condition(students["school_id"].value_counts().min() >= 20, "Each school should have at least 20 students.")
    assert_condition(events["student_id"].isin(students["student_id"]).all(), "Events contain unknown students.")
    assert_condition(assessments["student_id"].isin(students["student_id"]).all(), "Assessments contain unknown students.")
    assert_condition(events["minutes_spent"].between(0, 180).all(), "Event minutes outside expected range.")
    assert_condition(assessments["score"].between(0, 100).all(), "Assessment scores outside 0-100 range.")

    dropout_rate = students["dropped_out"].mean()
    assert_condition(0.12 <= dropout_rate <= 0.35, "Dropout rate is outside the expected synthetic range.")

    print("All quality checks passed.")
    print(f"Students: {len(students):,}")
    print(f"Schools: {len(schools):,}")
    print(f"Engagement events: {len(events):,}")
    print(f"Assessments: {len(assessments):,}")
    print(f"Dropout rate: {dropout_rate:.1%}")


if __name__ == "__main__":
    main()
