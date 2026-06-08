# Threshold Logic

This project uses explainable thresholds so a program manager can understand why a learner is assigned to a segment or intervention queue. The thresholds are simple by design and should be treated as starting points for stakeholder review.

## Engagement Segments

### Low Engagement

Threshold: `engagement_rate <= 30th percentile`

Reason: The bottom 30% identifies learners who are meaningfully below the cohort's normal participation level without labeling half the population as low engagement. This creates a focused intervention list that a school-success team could review weekly.

### High Engagement

Threshold: `engagement_rate >= 70th percentile`

Reason: The top 30% captures consistently active learners while allowing for normal variation across schools and grades. This threshold is used for enrichment and high-performer identification, not risk detection.

### Strong Academic Performance

Threshold: `avg_assessment_score >= 72`

Reason: A score above 72 indicates the learner is performing comfortably above the 60-point pass threshold. Combining this with high engagement identifies students who may benefit from enrichment rather than remediation.

### Academic Struggle

Threshold: `avg_assessment_score < 60`

Reason: The synthetic assessment table uses 60 as the pass threshold. Learners below this level need academic support even if they remain active in the platform.

### Declining Momentum

Threshold: `recent_sessions - early_sessions < 0`

Reason: A negative change in session volume is an early-warning signal. It catches learners whose cumulative activity may still look acceptable but whose recent behavior is deteriorating.

## Risk Score

The risk score ranges from 0 to 1 in the Python feature table. It weights:

- Low active-day rate
- Inactive days since last activity
- Declining engagement momentum
- Low pass rate
- Poor internet quality

Threshold: `risk_score >= 0.62`

Reason: In the generated dataset, this threshold produces a high-priority review group of roughly 10-15% of learners. That is large enough to catch meaningful risk but small enough to be operationally reviewable each week.

## Why These Thresholds Are Visible

This case study is designed for operational analytics. For a school-success workflow, explainability matters: teams need to know whether a learner is flagged because of inactivity, academic struggle, declining momentum, or access constraints. A predictive model could be added later, but these rules provide a transparent first version for stakeholder review.
