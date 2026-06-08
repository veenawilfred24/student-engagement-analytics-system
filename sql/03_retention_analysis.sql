/*
Retention cohort analysis

Purpose:
Measure whether students were active during specific windows after enrollment.
This avoids a weak shortcut where "week 1 retention" is calculated from total
term activity.

Dialect: PostgreSQL
*/

WITH activity_relative_to_enrollment AS (
    SELECT
        s.student_id,
        s.school_id,
        s.grade,
        s.socioeconomic_band,
        DATE_TRUNC('week', s.enrollment_date::DATE) AS enrollment_week,
        e.event_date::DATE - s.enrollment_date::DATE AS days_since_enrollment,
        e.event_date::DATE AS activity_date
    FROM students s
    LEFT JOIN engagement_events e
        ON s.student_id = e.student_id
),
student_retention AS (
    SELECT
        student_id,
        school_id,
        grade,
        socioeconomic_band,
        enrollment_week,
        COUNT(DISTINCT activity_date) AS term_active_days,
        COUNT(DISTINCT CASE WHEN days_since_enrollment BETWEEN 0 AND 6 THEN activity_date END) AS week_1_active_days,
        COUNT(DISTINCT CASE WHEN days_since_enrollment BETWEEN 7 AND 13 THEN activity_date END) AS week_2_active_days,
        COUNT(DISTINCT CASE WHEN days_since_enrollment BETWEEN 0 AND 29 THEN activity_date END) AS month_1_active_days,
        COUNT(DISTINCT CASE WHEN days_since_enrollment BETWEEN 60 AND 89 THEN activity_date END) AS final_month_active_days
    FROM activity_relative_to_enrollment
    GROUP BY student_id, school_id, grade, socioeconomic_band, enrollment_week
)
SELECT
    enrollment_week,
    grade,
    socioeconomic_band,
    COUNT(*) AS cohort_size,
    ROUND(AVG(CASE WHEN week_1_active_days >= 1 THEN 1.0 ELSE 0.0 END), 3) AS week_1_activation_rate,
    ROUND(AVG(CASE WHEN week_2_active_days >= 1 THEN 1.0 ELSE 0.0 END), 3) AS week_2_return_rate,
    ROUND(AVG(CASE WHEN month_1_active_days >= 7 THEN 1.0 ELSE 0.0 END), 3) AS month_1_retention_rate,
    ROUND(AVG(CASE WHEN final_month_active_days >= 4 THEN 1.0 ELSE 0.0 END), 3) AS final_month_retention_rate,
    ROUND(AVG(term_active_days), 1) AS avg_term_active_days
FROM student_retention
GROUP BY enrollment_week, grade, socioeconomic_band
HAVING COUNT(*) >= 25
ORDER BY enrollment_week, grade, socioeconomic_band;
