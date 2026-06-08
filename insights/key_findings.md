# Key Findings

## Executive Summary

The synthetic dataset covers 5,000 learners across 100 schools, with a modeled term dropout rate of 21.9%. The strongest operating signals are not single login counts; they are engagement momentum, retention by grade, school-level execution differences, and access-related support barriers.

## Insight 1: Engagement Momentum Predicts Near-Term Drop-off

**Segment:** Learners with declining engagement momentum across the term.

**Comparison:** Students with declining momentum show a 32.0% dropout rate, compared with 0.1% for students with improving momentum.

**Implication:** A student can look active early in the term and still become a dropout risk if recent sessions fall. Weekly reporting should not rely only on cumulative activity.

**Recommended action:** Build a weekly intervention queue for students with negative momentum, especially when paired with 14+ inactive days or low pass rates. Outreach should happen before the dropout date, not after the term-end retention report.

## Insight 2: Upper Grades Show Higher Retention Risk

**Segment:** Grades 10-12.

**Comparison:** Grade 12 has the highest dropout rate at 24.7%, while Grade 8 has the lowest at 19.0%. Grade 12 also has a lower active-day rate at 55.0%, compared with 60.6% for Grade 8.

**Implication:** Older students may face competing priorities, exam pressure, or reduced program fit. Treating all grades with the same engagement strategy hides this difference.

**Recommended action:** Create grade-specific outreach plans for Grades 10-12. Shorten re-engagement cycles, add exam-aligned content prompts, and monitor final-month activity separately for upper grades.

## Insight 3: Connectivity Constraints Compound Dropout Risk

**Segment:** Learners marked with poor internet quality.

**Comparison:** Poor-internet learners show a 32.2% dropout rate, compared with 16.7% for learners with good internet quality. The gap is largest in Grade 9, where poor-internet learners drop at 39.1% versus 15.4% for good-internet learners.

**Implication:** Connectivity is not just a background demographic field; it changes how likely a learner is to sustain activity. The same reminder cadence will underperform for students who cannot reliably access content.

**Recommended action:** Add low-bandwidth nudges, offline completion options, and guardian outreach for poor-connectivity learners. Track this group separately in the at-risk dashboard to avoid mistaking access friction for low motivation.

## Insight 4: School Type Differences Point to Support Prioritization

**Segment:** School type.

**Comparison:** Charter schools have the highest modeled dropout rate at 24.7%, compared with 19.7% for private schools. Charter schools also show a lower average active-day rate at 57.8%, compared with 60.3% for private schools.

**Implication:** School-level operating context affects learner engagement. A school-success team should not only look at individual student behavior; it should examine implementation quality, staffing, and school routines.

**Recommended action:** Use school type as a diagnostic lens when reviewing bottom-quartile schools. Prioritize coaching sessions for schools with high dropout, low active-day rate, and above-average high-risk learner counts.

## Insight 5: Funnel Retention Weakens in Upper Grades After Assignment Submission

**Segment:** Learners who reached the assignment-submission stage, split by grade.

**Comparison:** Grade 12 shows the highest assignment-to-retention drop-off at 27.2%, compared with 20.0% for Grade 8. Grade 11 follows at 26.2%, and Grade 10 at 25.3%.

**Implication:** The issue is not only initial activation; many upper-grade learners complete enough activity to submit assignments but still fail to retain through the term. That suggests content pacing, workload, or perceived value may be breaking down after meaningful participation.

**Recommended action:** Review upper-grade assignment length, difficulty, and timing. Add scaffolded support before assignment due dates and test shorter reinforcement modules for Grades 10-12.

## Insight 6: Bottom-Quartile Schools Need Operational Review, Not Just Student Outreach

**Segment:** Schools in the bottom quartile of the engagement index.

**Comparison:** Bottom-quartile schools average a 31.7% dropout rate and 51.8% active-day rate. Top-quartile schools average a 15.1% dropout rate and 66.1% active-day rate.

**Implication:** Student-level interventions alone will not close the gap if school-level implementation is weak. The school ranking should trigger a different workflow from the student risk queue.

**Recommended action:** For bottom-quartile schools, run an implementation review covering teacher routines, digital readiness, content completion cadence, and weekly monitoring. Track whether the school improves in rank over the next reporting cycle.

## Caveats

- The dataset is synthetic and designed for portfolio demonstration.
- Risk scoring is explainable and rule-based; it is not a validated predictive model.
- Socioeconomic and access-related variables are used to identify support needs and would require privacy and fairness review in a real deployment.
