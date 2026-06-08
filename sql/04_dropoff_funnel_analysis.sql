/*
Drop-off funnel analysis

Purpose:
Translate raw activity into operational funnel stages. The final output includes
both stage counts and step-to-step conversion rates.

Dialect: PostgreSQL
*/

WITH student_activity AS (
    SELECT
        s.student_id,
        s.school_id,
        s.grade,
        s.dropped_out,
        COUNT(DISTINCT e.event_date::DATE) AS active_days,
        COUNT(e.event_id) AS sessions,
        COALESCE(SUM(e.minutes_spent), 0) AS minutes_spent,
        COALESCE(SUM(CASE WHEN e.activity_type = 'lesson_view' THEN 1 ELSE 0 END), 0) AS lesson_views,
        COALESCE(SUM(CASE WHEN e.activity_type = 'quiz_attempt' THEN 1 ELSE 0 END), 0) AS quiz_attempts,
        COALESCE(SUM(CASE WHEN e.activity_type = 'assignment_submit' THEN 1 ELSE 0 END), 0) AS assignment_submits
    FROM students s
    LEFT JOIN engagement_events e
        ON s.student_id = e.student_id
    GROUP BY s.student_id, s.school_id, s.grade, s.dropped_out
),
funnel_flags AS (
    SELECT
        *,
        1 AS enrolled,
        CASE WHEN sessions >= 1 THEN 1 ELSE 0 END AS activated,
        CASE WHEN active_days >= 3 THEN 1 ELSE 0 END AS reached_three_active_days,
        CASE WHEN lesson_views >= 5 THEN 1 ELSE 0 END AS consumed_core_lessons,
        CASE WHEN quiz_attempts >= 3 THEN 1 ELSE 0 END AS practiced_with_quizzes,
        CASE WHEN assignment_submits >= 1 THEN 1 ELSE 0 END AS submitted_assignment,
        CASE WHEN active_days >= 21 AND NOT dropped_out THEN 1 ELSE 0 END AS retained
    FROM student_activity
),
school_grade_funnel AS (
    SELECT
        school_id,
        grade,
        COUNT(*) AS enrolled,
        SUM(activated) AS activated,
        SUM(reached_three_active_days) AS reached_three_active_days,
        SUM(consumed_core_lessons) AS consumed_core_lessons,
        SUM(practiced_with_quizzes) AS practiced_with_quizzes,
        SUM(submitted_assignment) AS submitted_assignment,
        SUM(retained) AS retained
    FROM funnel_flags
    GROUP BY school_id, grade
)
SELECT
    school_id,
    grade,
    enrolled,
    activated,
    reached_three_active_days,
    consumed_core_lessons,
    practiced_with_quizzes,
    submitted_assignment,
    retained,
    ROUND(activated::NUMERIC / NULLIF(enrolled, 0), 3) AS enrolled_to_activated_rate,
    ROUND(reached_three_active_days::NUMERIC / NULLIF(activated, 0), 3) AS activated_to_three_day_rate,
    ROUND(consumed_core_lessons::NUMERIC / NULLIF(reached_three_active_days, 0), 3) AS three_day_to_lessons_rate,
    ROUND(practiced_with_quizzes::NUMERIC / NULLIF(consumed_core_lessons, 0), 3) AS lessons_to_quiz_rate,
    ROUND(submitted_assignment::NUMERIC / NULLIF(practiced_with_quizzes, 0), 3) AS quiz_to_assignment_rate,
    ROUND(retained::NUMERIC / NULLIF(submitted_assignment, 0), 3) AS assignment_to_retained_rate
FROM school_grade_funnel
ORDER BY assignment_to_retained_rate ASC NULLS LAST, enrolled DESC;
