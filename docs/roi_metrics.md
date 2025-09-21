# ROI Metrics Reference

The ROI analytics endpoint backs the CAD dashboard panels.  Metrics are
calculated from overlay review activity and the audit logs captured during
exports.  Each event records a manual baseline estimate (in seconds), the
automated duration, and the number of accepted suggestions delivered.

| Metric | Description |
| --- | --- |
| `automation_score` | Blended score combining decision acceptance rate and the share of baseline review time saved through automation.  Values are normalised between `0` and `1`. |
| `savings_percent` | Percentage of manual review time avoided across overlay runs, decisions and exports. |
| `review_hours_saved` | Total hours of reviewer effort avoided compared to the manual baseline. |
| `payback_weeks` | Estimated number of weeks to recover a notional 40 hour onboarding investment.  Falls as saved hours increase. |
| `iterations` | Count of overlay-related events (`overlay_run`, `overlay_decision`, `overlay_export`) recorded for the project. |
| `acceptance_rate` | Share of overlay decisions marked as approved. |
| `event_count` | Total audit events available for the ROI snapshot. |
| `baseline_hours` / `automated_hours` | Aggregated manual baseline versus automated execution hours backing the savings computation. |

The analytics module treats baselines and savings as additive across events, so
instrumentation should populate `baseline_seconds` and `automated_seconds` on
`project_audit_logs` entries.  Export flows should also store
`accepted_suggestions` to provide downstream dashboards with context about the
volume of automated deliverables.
