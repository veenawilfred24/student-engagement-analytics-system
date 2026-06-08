/*
School ranking model

Purpose:
Rank schools for school-success prioritization. The index is intentionally
transparent, with each component shown separately so a reviewer can challenge
or reweight the method.

Dialect: PostgreSQL
*/

WITH params AS (
    SELECT 90::NUMERIC AS term_days
),
student_engagement AS (
    SELECT
        st.student_id,
        st.school_id,
        COUNT(DISTINCT e.event_date::DATE) / p.term_days AS active_day_rate,
        COALESCE(SUM(e.minutes_spent), 0) AS total_minutes,
        COALESCE(SUM(e.content_items_completed), 0) AS content_completed,
        MAX(e.day_number) AS last_active_day
    FROM students st
    CROSS JOIN params p
    LEFT JOIN engagement_events e
        ON st.student_id = e.student_id
    GROUP BY st.student_id, st.school_id, p.term_days
),
assessment AS (
    SELECT
        student_id,
        AVG(score) AS avg_score,
        AVG(CASE WHEN passed THEN 1.0 ELSE 0.0 END) AS pass_rate
    FROM assessments
    GROUP BY student_id
),
school_metrics AS (
    SELECT
        sc.school_id,
        sc.school_name,
        sc.region,
        sc.school_type,
        sc.urbanicity,
        COUNT(st.student_id) AS student_count,
        AVG(se.active_day_rate) AS active_day_rate,
        AVG(CASE WHEN se.last_active_day >= 76 THEN 1.0 ELSE 0.0 END) AS recent_active_rate,
        AVG(se.total_minutes) AS minutes_per_student,
        AVG(se.content_completed) AS completions_per_student,
        AVG(COALESCE(a.avg_score, 0)) AS avg_assessment_score,
        AVG(COALESCE(a.pass_rate, 0)) AS pass_rate,
        AVG(CASE WHEN st.dropped_out THEN 1.0 ELSE 0.0 END) AS dropout_rate,
        AVG(sc.implementation_quality) / 100.0 AS implementation_quality_rate
    FROM schools sc
    JOIN students st
        ON sc.school_id = st.school_id
    LEFT JOIN student_engagement se
        ON st.student_id = se.student_id
    LEFT JOIN assessment a
        ON st.student_id = a.student_id
    GROUP BY sc.school_id, sc.school_name, sc.region, sc.school_type, sc.urbanicity
),
scored AS (
    SELECT
        *,
        active_day_rate * 35 AS engagement_points,
        recent_active_rate * 15 AS recency_points,
        (avg_assessment_score / 100.0) * 20 AS assessment_points,
        (1 - dropout_rate) * 20 AS retention_points,
        implementation_quality_rate * 10 AS implementation_points
    FROM school_metrics
)
SELECT
    school_id,
    school_name,
    region,
    school_type,
    urbanicity,
    student_count,
    ROUND(active_day_rate, 3) AS active_day_rate,
    ROUND(recent_active_rate, 3) AS recent_active_rate,
    ROUND(dropout_rate, 3) AS dropout_rate,
    ROUND(avg_assessment_score, 1) AS avg_assessment_score,
    ROUND(engagement_points, 2) AS engagement_points,
    ROUND(recency_points, 2) AS recency_points,
    ROUND(assessment_points, 2) AS assessment_points,
    ROUND(retention_points, 2) AS retention_points,
    ROUND(implementation_points, 2) AS implementation_points,
    ROUND(
        engagement_points
        + recency_points
        + assessment_points
        + retention_points
        + implementation_points,
        2
    ) AS engagement_index,
    RANK() OVER (
        ORDER BY
            engagement_points
            + recency_points
            + assessment_points
            + retention_points
            + implementation_points DESC
    ) AS school_rank
FROM scored
WHERE student_count >= 20
ORDER BY school_rank;
