# Demo Script – Capture to Marketing Pack

## Audience

- Internal leadership review
- Pilot agents invited to private beta
- Potential implementation partners (design, data, compliance)

## Length

- 15 minutes presentation + 5 minutes Q&A

## Environment Setup

- Staging frontend (`/agents/site-capture`) with seeded coordinates:
  - Harbourfront (mixed-use flagship) – *primary demo*
  - Telok Ayer heritage site – *backup*
- Browser prepared with marketing pack quickstart open (`docs/agents/marketing_pack_quickstart.md`).
- Pre-generated packs stored locally in case the live run needs a fallback.
- Screen recording enabled.

## Narrative Outline

1. **Problem Statement (2 min)**
   - Agents spend hours compiling feasibility notes before they can market a site.
   - Compliance wording is inconsistent, risking regulatory redlines.

2. **Live Journey (10 min)**
   1. *Capture:* Enter Harbourfront coordinates, submit with default scenarios.
   2. *Insights:* Highlight quick analysis headlines, scenario metrics, and amenity context.
   3. *Market intelligence:* Call out transactions and pipeline snapshot in sidebar.
   4. *Marketing pack:* Generate “Universal” pack, note loading state, download link, and file size.
   5. *Preview excerpt:* Show pre-downloaded PDF page with compliance disclaimers and summary metrics.

3. **Impact (2 min)**
   - Time saved per listing.
   - Ready-to-share collateral and consistent messaging.
   - Foundation for developer tooling (without committing to timelines).

4. **Next Steps (1 min)**
   - Live agent walkthroughs (reference `docs/validation/live_walkthrough_plan.md`).
   - Iterate based on captured feedback before enabling developer acquisition flow.

## Demo Checklist

- [ ] Verify staging data freshness morning of demo.
- [ ] Clear browser cache to avoid stale assets.
- [ ] Confirm PDF generator service health (test once one hour before session).
- [ ] Update slide with latest known limitations (no custom branding, limited transaction depth).
- [ ] Share quickstart link with attendees post-demo.

## Q&A Prep

| Topic | Talking Points |
| --- | --- |
| Data coverage | Seeded for Harbourfront, CBD, Jurong; more districts planned post-validation. |
| Custom branding | Roadmap item; current packs use neutral OB branding. |
| Offline usage | Exported PDF can be shared offline; capture flow requires connectivity. |
| Compliance review | Disclaimers sourced from approved language in `FEATURES.md`; legal review scheduled after pilot. |

