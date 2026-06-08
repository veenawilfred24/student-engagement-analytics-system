"""Generate synthetic data for the Student Engagement Analytics System.

The generator creates realistic, reproducible educational engagement data:
- 5,000 students
- 100 schools
- Daily engagement behavior over one academic term
- Dropout and retention patterns influenced by attendance, usage, and context

Run:
    python python/generate_data.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
N_STUDENTS = 5_000
N_SCHOOLS = 100
TERM_DAYS = 90

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


@dataclass(frozen=True)
class GenerationConfig:
    n_students: int = N_STUDENTS
    n_schools: int = N_SCHOOLS
    term_days: int = TERM_DAYS
    seed: int = RANDOM_SEED


def sigmoid(value: np.ndarray | float) -> np.ndarray | float:
    """Convert a linear risk score into a probability."""
    return 1 / (1 + np.exp(-value))


def create_schools(rng: np.random.Generator, config: GenerationConfig) -> pd.DataFrame:
    regions = ["North", "South", "East", "West", "Central"]
    school_types = ["Public", "Private", "Charter", "Low-cost Private"]
    urbanicity = ["Urban", "Suburban", "Rural"]

    schools = pd.DataFrame(
        {
            "school_id": [f"SCH{i:03d}" for i in range(1, config.n_schools + 1)],
            "school_name": [f"School {i:03d}" for i in range(1, config.n_schools + 1)],
            "region": rng.choice(regions, config.n_schools, p=[0.22, 0.2, 0.18, 0.2, 0.2]),
            "school_type": rng.choice(school_types, config.n_schools, p=[0.48, 0.22, 0.12, 0.18]),
            "urbanicity": rng.choice(urbanicity, config.n_schools, p=[0.42, 0.33, 0.25]),
            "teacher_student_ratio": np.round(rng.normal(1 / 32, 0.007, config.n_schools), 4),
            "digital_readiness_score": np.round(rng.beta(4, 2, config.n_schools) * 100, 1),
            "implementation_quality": np.round(rng.beta(5, 2.5, config.n_schools) * 100, 1),
        }
    )
    schools["teacher_student_ratio"] = schools["teacher_student_ratio"].clip(0.018, 0.055)
    return schools


def create_students(
    rng: np.random.Generator, schools: pd.DataFrame, config: GenerationConfig
) -> pd.DataFrame:
    grades = np.arange(6, 13)
    start_date = pd.Timestamp("2025-08-01")

    school_weights = rng.dirichlet(np.ones(config.n_schools) * 1.7)
    minimum_school_size = 20
    base_counts = np.repeat(minimum_school_size, config.n_schools)
    remaining_students = config.n_students - int(base_counts.sum())
    variable_counts = rng.multinomial(remaining_students, school_weights)
    school_counts = base_counts + variable_counts
    school_ids = np.repeat(schools["school_id"].to_numpy(), school_counts)
    rng.shuffle(school_ids)
    school_lookup = schools.set_index("school_id")

    students = pd.DataFrame(
        {
            "student_id": [f"STU{i:05d}" for i in range(1, config.n_students + 1)],
            "school_id": school_ids,
            "grade": rng.choice(grades, config.n_students, p=[0.14, 0.15, 0.16, 0.17, 0.16, 0.12, 0.10]),
            "gender": rng.choice(["Female", "Male", "Non-binary"], config.n_students, p=[0.49, 0.49, 0.02]),
            "socioeconomic_band": rng.choice(["Low", "Middle", "High"], config.n_students, p=[0.36, 0.46, 0.18]),
            "device_access": rng.choice(["Shared phone", "Own phone", "Tablet", "Laptop/Desktop"], config.n_students, p=[0.28, 0.34, 0.16, 0.22]),
            "internet_quality": rng.choice(["Poor", "Moderate", "Good"], config.n_students, p=[0.22, 0.45, 0.33]),
            "enrollment_date": start_date + pd.to_timedelta(rng.integers(0, 21, config.n_students), unit="D"),
        }
    )

    readiness = students["school_id"].map(school_lookup["digital_readiness_score"]) / 100
    implementation = students["school_id"].map(school_lookup["implementation_quality"]) / 100
    device_bonus = students["device_access"].map(
        {"Shared phone": -0.18, "Own phone": 0.00, "Tablet": 0.08, "Laptop/Desktop": 0.14}
    )
    internet_bonus = students["internet_quality"].map({"Poor": -0.18, "Moderate": 0.00, "Good": 0.12})
    income_bonus = students["socioeconomic_band"].map({"Low": -0.12, "Middle": 0.02, "High": 0.11})
    grade_effect = (students["grade"] - students["grade"].mean()) * -0.015

    baseline = 0.52 + readiness * 0.18 + implementation * 0.22 + device_bonus + internet_bonus + income_bonus + grade_effect
    students["baseline_engagement_score"] = np.round((baseline + rng.normal(0, 0.11, config.n_students)).clip(0.05, 0.98), 3)

    return students


def assign_dropout_status(rng: np.random.Generator, students: pd.DataFrame, schools: pd.DataFrame) -> pd.DataFrame:
    school_lookup = schools.set_index("school_id")
    implementation = students["school_id"].map(school_lookup["implementation_quality"]) / 100
    low_access = (students["device_access"] == "Shared phone").astype(int)
    poor_internet = (students["internet_quality"] == "Poor").astype(int)
    low_income = (students["socioeconomic_band"] == "Low").astype(int)
    senior_grade = students["grade"].ge(10).astype(int)

    linear_risk = (
        -2.35
        + (1 - students["baseline_engagement_score"]) * 3.2
        + low_access * 0.55
        + poor_internet * 0.46
        + low_income * 0.38
        + senior_grade * 0.22
        - implementation * 0.58
    )
    dropout_probability = sigmoid(linear_risk).clip(0.03, 0.72)
    did_dropout = rng.binomial(1, dropout_probability)
    dropout_day = np.where(did_dropout == 1, rng.triangular(18, 48, 88, len(students)).astype(int), np.nan)

    enriched = students.copy()
    enriched["dropout_probability"] = np.round(dropout_probability, 3)
    enriched["dropped_out"] = did_dropout.astype(bool)
    enriched["dropout_day"] = dropout_day
    enriched["dropout_date"] = pd.NaT
    mask = enriched["dropped_out"]
    enriched.loc[mask, "dropout_date"] = pd.Timestamp("2025-08-01") + pd.to_timedelta(
        enriched.loc[mask, "dropout_day"].astype(int), unit="D"
    )
    return enriched


def create_engagement_events(rng: np.random.Generator, students: pd.DataFrame, config: GenerationConfig) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    term_start = pd.Timestamp("2025-08-01")
    activity_types = ["lesson_view", "quiz_attempt", "assignment_submit", "video_watch", "discussion_post"]
    activity_probs = np.array([0.36, 0.20, 0.17, 0.22, 0.05])

    for row in students.itertuples(index=False):
        trend = rng.normal(-0.0008, 0.0025)
        for day in range(config.term_days):
            if row.dropped_out and day > row.dropout_day:
                continue

            weekday = (term_start + pd.Timedelta(days=day)).weekday()
            weekend_penalty = -0.22 if weekday >= 5 else 0.0
            pre_dropout_penalty = 0.0
            if row.dropped_out and day >= row.dropout_day - 14:
                pre_dropout_penalty = -0.018 * (day - (row.dropout_day - 14))

            daily_propensity = row.baseline_engagement_score + trend * day + weekend_penalty + pre_dropout_penalty
            active_probability = np.clip(daily_propensity, 0.01, 0.95)

            if rng.random() > active_probability:
                continue

            sessions = int(np.clip(rng.poisson(1 + active_probability * 2.1), 1, 7))
            minutes = rng.gamma(shape=2.1, scale=10 + active_probability * 14, size=sessions)
            for _ in range(sessions):
                activity = rng.choice(activity_types, p=activity_probs)
                records.append(
                    {
                        "event_id": f"EVT{len(records) + 1:08d}",
                        "student_id": row.student_id,
                        "school_id": row.school_id,
                        "event_date": term_start + pd.Timedelta(days=day),
                        "day_number": day + 1,
                        "activity_type": activity,
                        "minutes_spent": round(float(np.clip(rng.choice(minutes), 2, 120)), 1),
                        "content_items_completed": int(np.clip(rng.poisson(1 + active_probability * 3), 0, 12)),
                        "correct_answers": int(np.clip(rng.poisson(active_probability * 5), 0, 10)),
                        "attempted_questions": int(np.clip(rng.poisson(4 + active_probability * 6), 1, 15)),
                    }
                )

    events = pd.DataFrame(records)
    events["accuracy_rate"] = np.round(events["correct_answers"] / events["attempted_questions"], 3)
    return events


def create_assessments(rng: np.random.Generator, students: pd.DataFrame) -> pd.DataFrame:
    assessment_names = ["Diagnostic", "Unit 1", "Unit 2", "Midterm", "Unit 3", "Final"]
    assessment_days = [3, 18, 32, 48, 66, 86]
    rows: list[dict[str, object]] = []

    for student in students.itertuples(index=False):
        ability = np.clip(student.baseline_engagement_score + rng.normal(0, 0.12), 0.05, 0.98)
        for name, day in zip(assessment_names, assessment_days):
            if student.dropped_out and day > student.dropout_day:
                continue
            learning_gain = day / 86 * (0.13 + student.baseline_engagement_score * 0.10)
            score = np.clip((ability + learning_gain + rng.normal(0, 0.09)) * 100, 0, 100)
            rows.append(
                {
                    "student_id": student.student_id,
                    "school_id": student.school_id,
                    "assessment_name": name,
                    "assessment_date": pd.Timestamp("2025-08-01") + pd.Timedelta(days=day),
                    "score": round(float(score), 1),
                    "max_score": 100,
                    "passed": bool(score >= 60),
                }
            )

    return pd.DataFrame(rows)


def write_outputs(
    schools: pd.DataFrame, students: pd.DataFrame, events: pd.DataFrame, assessments: pd.DataFrame
) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    schools.to_csv(DATA_DIR / "schools.csv", index=False)
    students.to_csv(DATA_DIR / "students.csv", index=False)
    events.to_csv(DATA_DIR / "engagement_events.csv", index=False)
    assessments.to_csv(DATA_DIR / "assessments.csv", index=False)

    summary = pd.DataFrame(
        [
            {"metric": "students", "value": len(students)},
            {"metric": "schools", "value": len(schools)},
            {"metric": "engagement_events", "value": len(events)},
            {"metric": "assessments", "value": len(assessments)},
            {"metric": "dropout_rate", "value": round(students["dropped_out"].mean(), 4)},
        ]
    )
    summary.to_csv(DATA_DIR / "dataset_summary.csv", index=False)


def main() -> None:
    config = GenerationConfig()
    rng = np.random.default_rng(config.seed)

    schools = create_schools(rng, config)
    students = create_students(rng, schools, config)
    students = assign_dropout_status(rng, students, schools)
    events = create_engagement_events(rng, students, config)
    assessments = create_assessments(rng, students)
    write_outputs(schools, students, events, assessments)

    print("Synthetic data generated successfully.")
    print(f"Students: {len(students):,}")
    print(f"Schools: {len(schools):,}")
    print(f"Engagement events: {len(events):,}")
    print(f"Assessments: {len(assessments):,}")
    print(f"Dropout rate: {students['dropped_out'].mean():.1%}")


if __name__ == "__main__":
    main()
