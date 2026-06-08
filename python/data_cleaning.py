"""Clean and validate raw Student Engagement Analytics CSV data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"


def parse_boolean(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False})


def load_raw_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    return {
        "schools": pd.read_csv(data_dir / "schools.csv"),
        "students": pd.read_csv(data_dir / "students.csv"),
        "events": pd.read_csv(data_dir / "engagement_events.csv"),
        "assessments": pd.read_csv(data_dir / "assessments.csv"),
    }


def clean_students(students: pd.DataFrame) -> pd.DataFrame:
    cleaned = students.copy()
    cleaned["enrollment_date"] = pd.to_datetime(cleaned["enrollment_date"])
    cleaned["dropout_date"] = pd.to_datetime(cleaned["dropout_date"], errors="coerce")
    cleaned["dropped_out"] = parse_boolean(cleaned["dropped_out"])
    cleaned["dropout_day"] = pd.to_numeric(cleaned["dropout_day"], errors="coerce")
    cleaned["baseline_engagement_score"] = cleaned["baseline_engagement_score"].clip(0, 1)
    cleaned = cleaned.drop_duplicates(subset=["student_id"])
    return cleaned


def clean_events(events: pd.DataFrame) -> pd.DataFrame:
    cleaned = events.copy()
    cleaned["event_date"] = pd.to_datetime(cleaned["event_date"])
    numeric_columns = ["minutes_spent", "content_items_completed", "correct_answers", "attempted_questions", "accuracy_rate"]
    for column in numeric_columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    cleaned["minutes_spent"] = cleaned["minutes_spent"].clip(lower=0, upper=180)
    cleaned["accuracy_rate"] = cleaned["accuracy_rate"].clip(0, 1)
    cleaned = cleaned.dropna(subset=["event_id", "student_id", "school_id", "event_date"])
    cleaned = cleaned.drop_duplicates(subset=["event_id"])
    return cleaned


def clean_assessments(assessments: pd.DataFrame) -> pd.DataFrame:
    cleaned = assessments.copy()
    cleaned["assessment_date"] = pd.to_datetime(cleaned["assessment_date"])
    cleaned["score"] = pd.to_numeric(cleaned["score"], errors="coerce").clip(0, 100)
    cleaned["passed"] = parse_boolean(cleaned["passed"])
    return cleaned.dropna(subset=["student_id", "assessment_name", "score"])


def validate_referential_integrity(data: dict[str, pd.DataFrame]) -> None:
    student_ids = set(data["students"]["student_id"])
    school_ids = set(data["schools"]["school_id"])

    missing_event_students = set(data["events"]["student_id"]) - student_ids
    missing_event_schools = set(data["events"]["school_id"]) - school_ids
    missing_assessment_students = set(data["assessments"]["student_id"]) - student_ids

    if missing_event_students or missing_event_schools or missing_assessment_students:
        raise ValueError("Referential integrity check failed for one or more raw datasets.")


def save_clean_data(data: dict[str, pd.DataFrame], output_dir: Path = PROCESSED_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in data.items():
        frame.to_csv(output_dir / f"{name}_clean.csv", index=False)


def main() -> None:
    raw = load_raw_data()
    cleaned = {
        "schools": raw["schools"].drop_duplicates(subset=["school_id"]),
        "students": clean_students(raw["students"]),
        "events": clean_events(raw["events"]),
        "assessments": clean_assessments(raw["assessments"]),
    }
    validate_referential_integrity(cleaned)
    save_clean_data(cleaned)
    print(f"Clean data saved to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
