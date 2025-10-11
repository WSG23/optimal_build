# Agent Marketing Pack Quickstart

This guide walks agents through the end-to-end workflow from GPS capture to generating professional marketing packs in the staging environment.

## Prerequisites

- Access to the Agent workspace (`/agents/site-capture`) with staging credentials.
- Seeded coordinates from the pilot dataset (Harbourfront, CBD, or Jurong).
- Stable network connection for asset download.

## Workflow Overview

1. **Capture the site**
   - Enter latitude/longitude in the GPS capture form and keep all default scenarios selected.
   - Submit to generate quick analysis cards, amenities, and market intelligence contextual data.

2. **Review quick analysis output**
   - Confirm the scenario headlines align with the development story you expect to tell.
   - Note any missing metrics or confusing labels; these should be logged during the validation session.

3. **Trigger marketing pack generation**
   - In the “Professional marketing packs” sidebar, select the pack type that matches your objective:
     - *Universal* – general purpose deck with zoning, metrics, and compliance notes.
     - *Investment* – capital stack, financial sensitivities, and investor positioning.
     - *Sales* – buyer-focused highlights and comparable transactions.
     - *Lease* – tenant mix, absorption, and rent comparables.
   - Click **Generate professional pack** and wait for the confirmation state.

4. **Download and review**
   - Use the generated link to download the PDF.
   - Check disclaimers, data accuracy, and visual hierarchy before sharing externally.

## Validation Talking Points

- Does the generated pack cover the narrative you typically deliver to clients?
- Are disclaimers and compliance statements positioned appropriately?
- Which data needs refinement before the pack is production-ready?

## Troubleshooting

| Symptom | Suggested Action |
| --- | --- |
| Pack fails to generate | Re-run after refreshing the page. If failures persist, collect console logs and open an issue tagged `agent-validation`. |
| Missing download URL | Note the pack type and timestamp; attach to follow-up ticket for the engineering team. |
| Data discrepancies | Capture screenshots with expected versus actual values for the analytics backlog. |

## Next Steps After Each Session

- Record feedback in the [live walkthrough plan](../validation/live_walkthrough_plan.md).
- File actionable issues in the tracker (labels: `agent-validation`, `marketing-pack`).
- Update go/no-go status before proceeding to developer tooling workstreams.
