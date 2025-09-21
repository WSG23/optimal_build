# ROI Metrics Overview

Frontend dashboards consume the `/api/v1/roi/{project_id}` endpoint to visualise
automation impact for overlay workflows. The service aggregates audit log events
and overlay decision metadata to derive a consistent set of metrics:

- **automation_score** – proportion of baseline manual effort avoided through
  automation. It is capped at 99 % to avoid displaying a perfect score even when
  the measured duration is negligible.
- **savings_percent** – convenience formatting of `automation_score` for charts
  and summary cards.
- **review_hours_saved** – cumulative hours of review time avoided across
  overlay evaluations, suggestion decisions, and export generation.
- **payback_weeks** – projected number of weeks required to recoup an assumed
  40 hour enablement effort, based on the current savings rate.
- **iterations** – number of overlay engine runs recorded for the project.
- **acceptance_rate** – share of overlay suggestions that were ultimately
  approved by reviewers.
- **baseline_hours** / **actual_hours** – raw aggregates used to validate
  automation score calculations.

## Instrumentation Assumptions

The ROI model relies on lightweight baselines captured whenever automation
pipelines execute:

| Workflow                           | Baseline assumption             |
| ---------------------------------- | ------------------------------- |
| Overlay evaluation run             | 30 minutes per source geometry  |
| Overlay suggestion review decision | 15 minutes per suggestion       |
| Export generation                  | 20 minutes per approved overlay |

Actual durations are recorded using monotonic clocks so that the same values can
be reused in local development and automated tests without relying on wall-clock
accuracy.

These heuristics are intentionally conservative and produce non-zero savings for
integration tests that execute immediately. Real deployments can tune the
constants in `app/core/metrics/roi.py` to match empirical data without altering
API contracts.
