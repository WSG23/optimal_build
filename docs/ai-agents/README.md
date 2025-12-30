# AI Agent Playbooks

Extended persona playbooks for `optimal_build`. These provide deeper guidance beyond the `MCP.md` checklists.

## Quick Reference

| Document | Purpose |
|----------|---------|
| [MCP.md](../../MCP.md) | Core directives, persona summaries, agent roster |
| [CLAUDE.md](../../CLAUDE.md) | Claude-specific instructions and workflows |
| [_TEMPLATE.md](./_TEMPLATE.md) | Template for creating new playbooks |

## Playbook Index

### Core Development Personas

| Persona | File | When to Use |
|---------|------|-------------|
| Product Owner | [product_owner.md](./product_owner.md) | New features, acceptance criteria, backlog |
| Architect | [architect.md](./architect.md) | System design, integrations, patterns |
| Tech Lead | [tech_lead.md](./tech_lead.md) | Code quality, refactoring, standards |
| QA Engineer | [qa_engineer.md](./qa_engineer.md) | Testing, edge cases, coverage |
| UI/UX Designer | [ui_ux_designer.md](./ui_ux_designer.md) | User interfaces, flows, aesthetics |
| Documentation Specialist | [documentation_specialist.md](./documentation_specialist.md) | Docs, ADRs, examples |

### Security & Compliance

| Persona | File | When to Use |
|---------|------|-------------|
| Security Engineer | [security_engineer.md](./security_engineer.md) | Auth, validation, threats |
| Privacy/Compliance Officer | [privacy_compliance_officer.md](./privacy_compliance_officer.md) | PII, retention, regulations |
| Legal/Regulatory Analyst | [legal_regulatory_analyst.md](./legal_regulatory_analyst.md) | Zoning, permits, compliance |

### Infrastructure & Operations

| Persona | File | When to Use |
|---------|------|-------------|
| DevOps Engineer | [devops_engineer.md](./devops_engineer.md) | CI/CD, infra, deployments |
| Observability/SRE Engineer | [observability_sre_engineer.md](./observability_sre_engineer.md) | Monitoring, alerts, SLOs |
| Incident Commander | [incident_commander.md](./incident_commander.md) | Rollback, recovery, risk |
| Release Manager | [release_manager.md](./release_manager.md) | Releases, coordination |
| Performance Engineer | [performance_engineer.md](./performance_engineer.md) | Speed, latency, optimization |
| Cost Optimization Engineer | [cost_optimization_engineer.md](./cost_optimization_engineer.md) | Cloud spend, efficiency |

### Data & Analytics

| Persona | File | When to Use |
|---------|------|-------------|
| Data Scientist | [data_scientist.md](./data_scientist.md) | ML models, analytics |
| Data Governance Steward | [data_governance_steward.md](./data_governance_steward.md) | Ownership, lineage, contracts |
| Data Quality Analyst | [data_quality_analyst.md](./data_quality_analyst.md) | Validation, quality, drift |

### Domain Specialists

| Persona | File | When to Use |
|---------|------|-------------|
| Domain Expert | [domain_expert.md](./domain_expert.md) | Real estate logic, calculations |
| Finance/Underwriting Specialist | [finance_underwriting_specialist.md](./finance_underwriting_specialist.md) | Valuations, yields, formulas |
| Geospatial Specialist | [geospatial_specialist.md](./geospatial_specialist.md) | Maps, CRS, spatial queries |
| Sustainability/ESG Analyst | [sustainability_esg_analyst.md](./sustainability_esg_analyst.md) | Carbon, certifications, ESG |

### User Experience & Content

| Persona | File | When to Use |
|---------|------|-------------|
| Accessibility Specialist | [accessibility_specialist.md](./accessibility_specialist.md) | WCAG, keyboard, screen readers |
| Localization/Content Strategist | [localization_content_strategist.md](./localization_content_strategist.md) | i18n, copy, units |
| Documentation Specialist | [documentation_specialist.md](./documentation_specialist.md) | Docs, ADRs, examples |
| Training/Enablement Lead | [training_enablement_lead.md](./training_enablement_lead.md) | Guides, demos, onboarding |
| Support/Success Advocate | [support_success_advocate.md](./support_success_advocate.md) | Errors, FAQs, feedback |

## Playbook Structure

Each playbook follows this structure:

```markdown
# Persona: [Name]

**When to engage:** [Trigger conditions]

**Entry:** [Prerequisites]
**Exit:** [Deliverables]

**Auto-summon triggers:** [Change types that must pull this persona in]
**Blockers:** [Conditions that block shipping, tied to MCP Quality → Testing → Security → User value]

**Do:** [Best practices]
**Anti-patterns:** [Mistakes to avoid]
**Required artifacts/tests:** [Deliverables]
**Workflows & tests to trigger:** [Feature, bug, migration, UI, external I/O]
**Artifacts/evidence to attach (PR/ADR):** [Test runs, metrics, citations, screenshots, rollback/flags]
**Collaborates with:** [Related personas]
**Example tasks:** [Concrete examples]
**Domain-specific notes:** [optimal_build context]
```

## Creating New Playbooks

1. Copy [_TEMPLATE.md](./_TEMPLATE.md)
2. Fill in all sections
3. Add entry to this README
4. Add persona to [MCP.md](../../MCP.md) Section 2

## Persona coverage checklist (for PRs/CI)

- Auto-summon personas by change type: Security (new external I/O, auth/logging changes), Performance (large payloads, render loops), Release Manager (migrations), Accessibility (UI changes), QA (all behavior changes), Documentation Specialist (user-facing/API changes).
- Tests attached per persona guidance: regression IDs, integration/contract tests, a11y checks, perf benchmarks, schema validation/migration guards.
- Evidence linked in PR: test runs, metrics/benchmarks, citations/assumptions, UI/a11y screenshots, rollout/rollback notes.
- Docs/acceptance updated when user-facing or contract changes occur (see `MCP.md`, `CODING_RULES.md`, `docs/all_steps_to_product_completion.md`).

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.2 | 2025-12-10 | Added coverage checklist, expanded structure (auto-summon, blockers, evidence), and finished remaining persona docs |
| 1.1 | 2025-12-10 | Added cross-references, enhanced all playbooks, added 3 new personas |
| 1.0 | Initial | Basic playbook structure |
