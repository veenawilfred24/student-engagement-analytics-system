/*
At-risk student detection

Purpose:
Create a transparent intervention queue. Socioeconomic and access variables are
included as support-context flags, not as reasons to deny service. In a real
deployment, this query would require fairness review and monitoring.

Dialect: PostgreSQL
*/

WITH engagement_windows AS (
    SELECT
        s.student_id,
        s.school_id,
        s.grade,
        s.device_access,
        s.internet_quality,
        s.socioeconomic_band,
        s.dropped_out,
        COUNT(DISTINCT CASE WHEN e.day_number BETWEEN 1 AND 30 THEN e.event_date::DATE END) AS early_active_days,
        COUNT(DISTINCT CASE WHEN e.day_number BETWEEN 61 AND 90 THEN e.event_date::DATE END) AS recent_active_days,
        MAX(e.day_number) AS last_active_day,
        AVG(e.accuracy_rate) AS avg_accuracy,
        SUM(e.minutes_spent) AS total_minutes
    FROM students s
    LEFT JOIN engagement_events e
        ON s.student_id = e.student_id
    GROUP BY
        s.student_id,
        s.school_id,
        s.grade,
        s.device_access,
        s.internet_quality,
        s.socioeconomic_band,
        s.dropped_out
),
assessment_summary AS (
    SELECT
        student_id,
        AVG(score) AS avg_score,
        AVG(CASE WHEN passed THEN 1.0 ELSE 0.0 END) AS pass_rate
    FROM assessments
    GROUP BY student_id
),
risk_scoring AS (
    SELECT
        ew.*,
        COALESCE(a.avg_score, 0) AS avg_score,
        COALESCE(a.pass_rate, 0) AS pass_rate,
        90 - COALESCE(ew.last_active_day, 0) AS inactive_days,
        CASE WHEN COALESCE(ew.recent_active_days, 0) < COALESCE(ew.early_active_days, 0) THEN 1 ELSE 0 END AS declining_engagement_flag,
        CASE WHEN 90 - COALESCE(ew.last_active_day, 0) >= 14 THEN 1 ELSE 0 END AS inactive_14_day_flag,
        CASE WHEN COALESCE(a.pass_rate, 0) < 0.50 THEN 1 ELSE 0 END AS low_pass_rate_flag,
        CASE WHEN ew.internet_quality = 'Poor' THEN 1 ELSE 0 END AS poor_internet_flag,
        CASE WHEN ew.device_access = 'Shared phone' THEN 1 ELSE 0 END AS shared_device_flag
    FROM engagement_windows ew
    LEFT JOIN assessment_summary a
        ON ew.student_id = a.student_id
),
scored AS (
    SELECT
        *,
        declining_engagement_flag * 25
        + inactive_14_day_flag * 25
        + low_pass_rate_flag * 20
        + poor_internet_flag * 15
        + shared_device_flag * 10
        + CASE WHEN socioeconomic_band = 'Low' THEN 5 ELSE 0 END AS risk_score_100
    FROM risk_scoring
)
SELECT
    student_id,
    school_id,
    grade,
    device_access,
    internet_quality,
    socioeconomic_band,
    early_active_days,
    recent_active_days,
    inactive_days,
    ROUND(avg_score, 1) AS avg_score,
    ROUND(pass_rate, 3) AS pass_rate,
    declining_engagement_flag,
    inactive_14_day_flag,
    low_pass_rate_flag,
    poor_internet_flag,
    shared_device_flag,
    risk_score_100,
    CASE
        WHEN risk_score_100 >= 70 THEN 'Critical'
        WHEN risk_score_100 >= 45 THEN 'High'
        WHEN risk_score_100 >= 25 THEN 'Moderate'
        ELSE 'Low'
    END AS risk_band,
    CASE
        WHEN inactive_14_day_flag = 1 THEN 'Call or message guardian within 48 hours'
        WHEN low_pass_rate_flag = 1 THEN 'Assign academic support'
        WHEN declining_engagement_flag = 1 THEN 'Send re-engagement nudge'
        ELSE 'Monitor'
    END AS recommended_action
FROM scored
WHERE NOT dropped_out
ORDER BY risk_score_100 DESC, inactive_days DESC, recent_active_days ASC;
