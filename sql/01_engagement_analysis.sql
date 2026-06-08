/*
Engagement analysis

Purpose:
Summarize school-level engagement while avoiding common portfolio-project
mistakes: hard-coded denominator logic, inflated averages from event-level joins,
and null-sensitive calculations.

Dialect: PostgreSQL
*/

WITH params AS (
    SELECT
        90::NUMERIC AS term_days,
        14::INTEGER AS recent_window_days
),
daily_student_activity AS (
    SELECT
        student_id,
        school_id,
        event_date::DATE AS activity_date,
        COUNT(*) AS sessions,
        SUM(minutes_spent) AS minutes_spent,
        SUM(content_items_completed) AS content_completed,
        AVG(accuracy_rate) AS avg_accuracy
    FROM engagement_events
    GROUP BY student_id, school_id, event_date::DATE
),
student_level AS (
    SELECT
        s.student_id,
        s.school_id,
        s.grade,
        s.socioeconomic_band,
        COUNT(d.activity_date) AS active_days,
        COALESCE(SUM(d.sessions), 0) AS total_sessions,
        COALESCE(SUM(d.minutes_spent), 0) AS total_minutes,
        COALESCE(SUM(d.content_completed), 0) AS content_completed,
        AVG(d.avg_accuracy) AS avg_accuracy,
        MAX(d.activity_date) AS last_active_date
    FROM students s
    LEFT JOIN daily_student_activity d
        ON s.student_id = d.student_id
    GROUP BY s.student_id, s.school_id, s.grade, s.socioeconomic_band
),
school_level AS (
    SELECT
        sl.school_id,
        COUNT(*) AS students,
        AVG(sl.active_days / p.term_days) AS active_day_rate,
        AVG(sl.total_sessions) AS sessions_per_student,
        AVG(sl.total_minutes) AS minutes_per_student,
        AVG(sl.content_completed) AS completions_per_student,
        AVG(sl.avg_accuracy) AS avg_accuracy,
        AVG(CASE WHEN sl.last_active_date >= DATE '2025-10-16' THEN 1.0 ELSE 0.0 END) AS recent_active_rate
    FROM student_level sl
    CROSS JOIN params p
    GROUP BY sl.school_id
)
SELECT
    sc.school_id,
    sc.school_name,
    sc.region,
    sc.school_type,
    sl.students,
    ROUND(sl.active_day_rate, 3) AS active_day_rate,
    ROUND(sl.recent_active_rate, 3) AS recent_active_rate,
    ROUND(sl.sessions_per_student, 1) AS sessions_per_student,
    ROUND(sl.minutes_per_student, 1) AS minutes_per_student,
    ROUND(sl.completions_per_student, 1) AS completions_per_student,
    ROUND(sl.avg_accuracy, 3) AS avg_accuracy
FROM school_level sl
JOIN schools sc
    ON sl.school_id = sc.school_id
ORDER BY active_day_rate DESC, recent_active_rate DESC;
