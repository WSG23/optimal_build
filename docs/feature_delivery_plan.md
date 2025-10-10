# Agent & Developer Feature Rollout Plan

This note captures the proposed approach for turning the high-level ideas in
`FEATURES.md` into working product increments. It focuses on starting small,
validating with real users, and expanding in clear stages so we can resume the
work even if this chat is lost later.

## 1. Start With A Flagship Experience

- **Why this matters:** Delivering one polished journey proves value to agents
  and gives the team confidence before tackling every tool described in the
  vision doc.
- **Recommendation:** Begin with the **Agent "Universal GPS Site Capture &
  Analysis"** flow. It covers mapping, property data, photos, and quick
  insights—enough surface area to validate user needs and system assumptions.

## 2. Discovery & Scoping Checklist

1. Interview several commercial agents and developers to confirm the value
   points (fast GPS capture, instant zoning context, quick reuse ideas).
2. Map the “happy path” for the first release: how someone captures a site,
   adds photos, and views a quick analysis summary.
3. Record regulatory guardrails (Singapore-only projects, compliance
   disclosures) so enforcement is built in from day one.

## 3. Experience Design (Plain Language)

- Sketch lightweight mockups for:
  - GPS logging screen.
  - Photo capture with auto-location tagging.
  - Quick analysis card showing zoning, potential GFA, and an illustrative 3D
    massing.
- Draft the text for compliance disclaimers using the wording already suggested
  in `FEATURES.md`.
- Decide how captured data flows into the Market Intelligence dashboard later so
  work isn’t redone.

## 4. Data & Foundations

- Gather clean datasets: URA zoning tables, recent transactions, basic 3D
  templates.
- Define the exact rules that enforce the Singapore-only scope (postal code
  checks, licensing flags, etc.).
- Pick reliable storage for site records and photos so the prototype feels
  stable.

## 5. Minimum Viable Build

- Implement GPS capture with location lookup and zoning context.
- Generate a quick analysis summary (potential use mix, headline metrics, single
  3D preview).
- Support photo upload with timestamps and map pins.

## 6. Feedback Loop

- Run live walkthroughs with 2–3 agents. *(Plan/notes in `docs/validation/live_walkthrough_plan.md`; outreach template in `docs/validation/agent_outreach_email.md`.)*
- Capture their feedback on usefulness, wording, and speed.
- Refine the summaries, tighten compliance messaging, and iterate on any rough
  spots.

## 7. Broaden Scope Once The Core Is Loved

After the GPS capture journey feels strong and is validated, move to the next
sets of features, reusing the same data foundations:

1. **Market Intelligence Dashboard:** Feed captured sites into broader market
   analytics so agents see everything in one place.
2. **Professional Marketing Pack Generator:** Turn the analysis summary into
   ready-to-share presentations with the smart disclaimers from the feature doc.
3. **Developer Tools:** Reuse the lessons from the agent journey to build the
   developer-specific “Universal GPS Site Acquisition” flow without duplicating
   effort.

## 8. Quality Gates & Documentation

- Continue running `make verify` (format, lint, tests, coding rules) with every
  increment.
- After a slice passes verification, stage the changes and create a focused
  commit so each milestone stays shippable.
- Keep `CODING_RULES.md` in mind for migrations, async endpoints, and Singapore
  compliance changes.
- Follow the workflow in `CONTRIBUTING.md` (testing loops, pre-commit retry
  cycle, reviewer expectations) so each iteration lands cleanly.
- Update contributor docs and user-facing guides alongside the new features.
  - Agent quickstart for marketing packs available in
    `docs/agents/marketing_pack_quickstart.md`.

## 9. Launch Preparation

- Create demos and quick-start guides for agents and developers.
  - Capture-to-pack demo script available in `docs/demos/agents_capture_demo.md`.
- Plan a private beta (for example: a small group of Singapore-based agents)
  before a wider release.

## Completion Signals

- Agents can capture a site, add photos, and receive a useful quick analysis in
  minutes.
- Market dashboards and marketing packs reuse that data with minimal extra work.
- Developer tools share the same foundations and only add their unique needs.
- Tests, docs, and compliance checks stay green throughout the rollout.

## Recent Progress Snapshot

- Implemented scenario-aware quick analysis in the GPS capture backend service,
  accompanied by targeted async unit tests.
- Added the "Agent GPS capture" workspace in the frontend so advisors can input
  coordinates, review scenario cards, and share insights with downstream teams.
- Enriched the quick analysis with nearby development pipeline, transaction and
  rental signals and exposed them in the UI with map/amenity context and
  workflow hand-offs.
- Extended the finance workspace to surface capital stack ratios and drawdown
  schedules end-to-end, covering backend calculations, API mapping, and UI
  visualisations.
- Documented linting/testing workflows and kept `make verify` as the default
  quality gate after each increment.
- Wired the agent capture workspace to property-specific market intelligence
  and unlocked one-click generation of universal, investment, sales, or leasing
  marketing packs with immediate download feedback.
- Extended the feasibility wizard so developers can generate those marketing
  packs directly when a captured property identifier is available.

This plan should make it easy to resume the conversation later and keep the team
aligned on what “start” and “finish” look like for the flagship features.
