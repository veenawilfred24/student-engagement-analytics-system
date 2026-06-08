# Power BI Dashboard Design

## Purpose

This dashboard is designed for weekly academic operations review. It should help teams decide which learners need outreach, which schools need implementation support, and where engagement drops in the learner journey.

## Audience

- Program leadership: system health, retention, and school performance.
- School-success managers: school prioritization and coaching needs.
- Academic operations: learner intervention queues and assessment-support needs.
- Data reviewers: metric definitions, model assumptions, and reproducibility.

## Data Model

Recommended model: star schema.

Fact tables:

- `engagement_events`
- `assessments`

Dimension tables:

- `students`
- `schools`

Derived analytical tables:

- `student_features`
- `student_segments`
- `school_engagement_rankings`

Relationships:

- `students[student_id]` 1-to-many `engagement_events[student_id]`
- `students[student_id]` 1-to-many `assessments[student_id]`
- `schools[school_id]` 1-to-many `students[school_id]`
- `students[student_id]` 1-to-1 `student_features[student_id]`
- `students[student_id]` 1-to-1 `student_segments[student_id]`

## Metric Definitions

```DAX
Students = DISTINCTCOUNT(students[student_id])

Schools = DISTINCTCOUNT(schools[school_id])

Active Students = DISTINCTCOUNT(engagement_events[student_id])

Active Day Rate = AVERAGE(student_features[engagement_rate])

Dropout Rate =
DIVIDE(
    CALCULATE(COUNTROWS(students), students[dropped_out] = TRUE()),
    COUNTROWS(students)
)

High Risk Students =
CALCULATE(
    DISTINCTCOUNT(student_features[student_id]),
    student_features[risk_score] >= 0.62
)

Average Assessment Score = AVERAGE(student_features[avg_assessment_score])

Engagement Index = AVERAGE(school_engagement_rankings[engagement_index])
```

## Page 1: Executive Overview

Business question: Is the program healthy this week?

Visuals:

- KPI cards: Students, Schools, Active Day Rate, Dropout Rate, High Risk Students, Average Assessment Score.
- Line chart: daily active students by event date.
- Bar chart: engagement index by region.
- Ranked bar chart: top 10 and bottom 10 schools.
- Small table: bottom-quartile schools with dropout rate, active-day rate, and high-risk learners.

Required slicers:

- Region
- School type
- Grade
- Socioeconomic band
- Device access
- Internet quality

## Page 2: Drop-off Funnel

Business question: Where do learners stop progressing?

Visuals:

- Funnel: enrolled, activated, three active days, core lesson consumption, quiz practice, assignment submission, retained.
- Matrix: funnel conversion by school and grade.
- Bar chart: assignment-to-retained rate by school type.
- Tooltip: school profile with cohort size, implementation quality, active-day rate, dropout rate.

## Page 3: School Ranking

Business question: Which schools need support first?

Visuals:

- Ranking table: school rank, engagement index, component points, dropout rate, active-day rate, assessment score.
- Scatter plot: implementation quality vs active-day rate; size by student count; color by dropout rate.
- Bar chart: high-risk students by school.
- Drillthrough: school detail page with segment mix and trend.

Design note:

Use the ranking as a prioritization input. Avoid labeling schools as failures; the operational action is coaching, implementation support, or resource review.

## Page 4: At-Risk Students

Business question: Who needs outreach this week, and why?

Visuals:

- Intervention table: student ID, school, grade, risk score, risk band, inactive days, recent active days, pass rate, recommended action.
- Stacked bar: risk band by grade.
- Bar chart: high-risk learners by internet quality and device access.
- Drillthrough: individual learner activity trend and assessment history.

Governance note:

Sensitive and access-related variables should be used to improve support, not to reduce service. Any real use would need privacy and fairness review.

## Page 5: Segmentation

Business question: Which outreach strategy fits each learner group?

Visuals:

- Segment distribution bar chart.
- Segment profile table: learners, dropout rate, active-day rate, assessment score, risk score.
- Scatter plot: engagement rate vs assessment score, colored by segment.
- Recommendation table:
  - Needs Re-engagement: contact sequence and low-bandwidth reminders.
  - Assessment Strugglers: academic support or tutoring.
  - Steady Participants: maintain cadence.
  - High Performers: enrichment and peer leadership opportunities.

## Design Standards

- Use neutral backgrounds with accessible contrast.
- Use teal for healthy engagement, amber for watchlist, red for high risk, and gray for context.
- Keep filters persistent on the left side.
- Use conditional formatting in ranking and risk tables.
- Make operational tables exportable.
- Do not display student names or personally identifying information.
