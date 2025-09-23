# Ingestion Overview

## How Buildable consumes ref_rules

The buildable screening service pulls approved, published zoning `ref_rules`
for the requested zone and merges them with zoning layers and request defaults.
Each rule contributes provenance data to the response, while the numeric
parameters shape the interim overrides that feed the calculation pipeline.

When multiple rules target the same parameter, Buildable applies a deterministic
precedence policy:

1. Rules tagged with a higher `override_priority` in their `source_provenance`
   win over lower priority entries. The ingestion flows use this to elevate
   manual adjustments captured as ref_rule overrides.
2. When `override_priority` is not provided, rules whose `seed_tag` is not the
   baseline `"zoning"` seed are treated as overrides and outrank the seeded
   defaults. This ensures ingested corrections take effect even when the static
   seed data remains in the catalogue.
3. Within the same priority tier, Buildable retains the most recently ingested
   rule (highest `id`) and ignores older entries. Seeded defaults continue to
   compare against each other using their original logic (e.g. the tightest plot
   ratio or widest setback wins) because they share the same priority.

Once an override has been applied for a parameter, lower-priority seed rules no
longer modify that override. As a result, the returned rule set always includes
both the seed entry and the override, while the metrics and setback overrides in
`calculate_buildable` reflect the ingested values rather than being replaced by
baseline seed data.
