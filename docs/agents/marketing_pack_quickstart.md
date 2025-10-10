# Agent GPS Capture & Marketing Pack Guide

This guide walks agents through the complete workflow for capturing a Singapore site, reviewing the quick analysis, and generating a professional marketing pack that can be shared with clients during the pilot phase.

## 1. Before You Start

- Access the Agent workspace at `/agents/site-capture` using the staging credentials provided by the product team.
- Keep the seeded coordinate list handy (Harbourfront, Telok Ayer, Jurong Industrial) so everyone sees the same data during validation.
- Ensure a stable network connection; marketing pack downloads are disabled offline.

> **Compliance reminder**
> Packs generated in staging are illustrative only. They must not be shared externally without explicit approval from the compliance team.

## 2. Navigate to the Capture Workspace

1. Sign in to the staging frontend.
2. From the sidebar, choose **Agent Capture**.
3. Confirm the header reads “Universal GPS site capture” and the marketing pack panel is visible on the right-hand side.

## 3. Capture a Site

1. Enter the latitude and longitude supplied for the session. They default to the CBD if left unchanged.
2. Leave all scenario checkboxes ticked unless the client conversation is tightly focused (e.g., heritage only).
3. Click **Generate quick analysis**. The request usually completes within 5–8 seconds.

When the capture succeeds you will see:
- Address details and existing use.
- Scenario cards (raw land, existing building, heritage, underused asset).
- Map tile centred on the coordinates.
- Nearby amenity call-outs.
- Market intelligence snapshot (transactions, pipeline, yields).

## 4. Review the Analysis

- Scan the scenario headlines and metrics. Note any values that look incorrect or confusing; these should be flagged during the feedback session.
- Check the disclaimers at the bottom of the page. They adapt to the scenarios returned (pre-development vs. sales/leasing language).
- Use the market intelligence panel to confirm transaction counts, pipeline projects, and yield benchmarks reflect the narrative you plan to tell.

## 5. Generate a Marketing Pack

1. In the **Professional marketing packs** card, pick the pack type:
   - **Universal** – balanced overview with zoning, scenarios, and compliance messaging.
   - **Investment** – capital structure, financing assumptions, and investor language.
   - **Sales** – positioning for buyers, comparables, and pricing signals.
   - **Lease** – tenant mix, absorption, and rental comparables.
2. Click **Generate professional pack**. A loading state appears while the PDF is assembled.
3. Once complete you’ll see the generation timestamp, file size estimate, and a download link (if enabled in the environment).

> Tip: keep the default pack type noted in your pipeline, so follow-on sessions start from the right context.

## 6. Download & Quality Check

1. Click the download link (opens in a new tab). Save the PDF locally.
2. Review the first three pages:
   - Cover story (title, address, compliance badge).
   - Key metrics summary.
   - Scenario outlooks with charts.
3. Skim the disclaimer page to confirm the wording matches your client’s distribution rules.
4. Capture any edits or data corrections that would make the pack client-ready and feed them back to the product team.

## 7. Troubleshooting & Known Limitations

| Symptom | Suggested Action |
| --- | --- |
| Pack fails to generate | Refresh the page and retry once. If it fails again, record the pack type, timestamp, and any console errors; file an issue tagged `marketing-pack`. |
| Download link missing | Some staging environments operate in restricted mode. Note the pack type and timestamp so engineering can retrieve the PDF from storage. |
| Analytics mismatch | Take a screenshot comparing expected vs. actual metrics and log under `agent-validation`. |
| Map does not load | Ensure `VITE_MAPBOX_ACCESS_TOKEN` is configured locally; otherwise use the map fallback text. |

## 8. Questions to Answer During Validation

- Does the quick analysis explain enough context for you to brief developers or investors?
- Is the marketing pack language ready for client conversations, or does it need rewording?
- Which metrics, charts, or disclaimers are missing for your asset type?
- How long did each step take, and where did you feel friction?

## 9. Feedback & Next Steps

- Document feedback in the [live walkthrough plan](../validation/live_walkthrough_plan.md) immediately after each session.
- File actionable improvements in the issue tracker with labels `agent-validation` and, if relevant, `marketing-pack`.
- Once at least two agents confirm the workflow meets expectations, we can move forward with developer tooling and documentation updates for contributors.

Need help? Contact the product or engineering lead listed with your session invite, or raise questions in the `#agents-pilot` channel.
