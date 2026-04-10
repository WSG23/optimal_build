# Capture Assumption Governance

## Purpose

This document defines how Capture should create, rank, display, and persist
starter-model assumptions.

Capture assumptions are preliminary inputs used to generate:
- starter massing
- scenario recommendations
- early engineering defaults

They are not compliance-certified or engineering-stamped outputs.

## Assumption Classes

Every assumption should be tagged with one source class:

1. `user_override`
   The user changed the value directly.
2. `property_specific`
   The value came from known property data.
3. `jurisdiction_default`
   The value came from location- and rules-aware defaults.
4. `learned`
   The value came from historical model learning or priors.
5. `heuristic_fallback`
   The value came from a generic rule when better inputs were absent.

## Precedence

Default precedence order:

1. `user_override`
2. `property_specific`
3. `jurisdiction_default`
4. `learned`
5. `heuristic_fallback`

This precedence applies to the active starter model shown to the user.

## Override Modes

Not every user change should be treated the same way.

### 1. Exploratory Override

Examples:
- user changes floor-to-floor height just to test feasibility
- user toggles a scenario to compare model outcomes
- user edits assumptions during one session without saving intent

Behavior:
- affects the current Capture session immediately
- outranks learned defaults for the current model
- does **not** update learned priors
- does **not** become a durable project default unless explicitly saved

### 2. Saved Project Override

Examples:
- user intentionally saves custom assumptions to a project
- user marks a preferred starter-model basis for this property

Behavior:
- affects future Capture/Feasibility work for that project
- still does **not** automatically become a portfolio-wide learned prior

### 3. Confirmed Learning Signal

Examples:
- repeated accepted overrides across many similar properties
- explicit user confirmation that a choice should inform future defaults

Behavior:
- can inform learned priors
- must remain auditable
- must never silently replace stronger rule/property inputs

## Learning Guardrails

Learned values may refine defaults, but must not:
- overwrite explicit user overrides
- hide their provenance
- exceed approved bounded ranges without review
- claim compliance or certified truth

Learned assumptions should be:
- bounded
- explainable
- reversible
- versioned when possible

## UI Wording Rules

Capture should use wording such as:
- `starter model assumptions`
- `preliminary defaults`
- `scenario-specific defaults`
- `rule-based`
- `inferred`

Capture should avoid wording such as:
- `certified`
- `validated`
- `approved`
- `compliance-grade`

unless the product later introduces a separate validated workflow with the
necessary evidence and legal/product approval.

## Immediate Implementation Policy

For the current Capture product:

- backend-generated starter-model assumptions are the source of truth for the
  active scenario preview
- frontend fallback assumptions are allowed only when backend assumptions are
  unavailable
- exploratory scenario changes should update the shown model and assumption
  summary immediately
- those exploratory changes should not be treated as learned defaults

## Future Expansion

Later phases can add:
- assumption provenance per field
- jurisdiction/version tagging
- property-specific confidence scores
- explicit save/apply controls for assumption overrides
- learning only from accepted or repeated override patterns
