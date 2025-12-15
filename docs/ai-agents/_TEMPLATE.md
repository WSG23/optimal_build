# Persona: [Name]

> **Template Version:** 1.0
>
> Use this template when creating new persona playbooks. Delete this block when done.

**When to engage:** [Trigger conditions - when should this persona be activated?]

**Entry:** [Prerequisites - what must be true before starting?]
**Exit:** [Deliverables - what must be completed before handoff?]

**Auto-summon triggers:** [Change types that must pull this persona in]
**Blockers:** [Conditions that block ship (tie to MCP Quality → Testing → Security → User value)]

**Do:**
- [Specific action 1]
- [Specific action 2]
- [Specific action 3]
- [Domain-specific best practice 1]
- [Domain-specific best practice 2]
- [Tool or technique recommendation]
- [Quality standard to maintain]
- [Documentation requirement]

**Anti-patterns:**
- [Common mistake 1]
- [Common mistake 2]
- [Common mistake 3]
- [Shortcut to avoid]
- [Misuse of tool or pattern]
- [Quality compromise to reject]

**Required artifacts/tests:**
- [Test type 1 (unit, integration, etc.)]
- [Documentation requirement]
- [Verification step]
- [Audit trail or log]
- [Review checklist item]

**Workflows & tests to trigger:**
- Feature build → [unit + integration + persona-specific]
- Bug fix → [regression test id]
- Migration → [migrate + downgrade guarded + data backfill test]
- UI change → [a11y checks, interaction tests]
- External I/O → [schema validation + fuzz tests]

**Artifacts/evidence to attach (PR/ADR):**
- [Links to test runs]
- [Profiles/benchmarks]
- [Citations/assumptions]
- [Screenshots for UI/a11y]
- [Checklist results or sign-offs]

**Collaborates with:**
- **[Persona 1]**: [Handoff reason or collaboration type]
- **[Persona 2]**: [Handoff reason or collaboration type]
- **[Persona 3]**: [Handoff reason or collaboration type]
- **[Persona 4]**: [Handoff reason or collaboration type]
- **[Persona 5]**: [Handoff reason or collaboration type]

**Example tasks:**
- [Concrete task example 1]
- [Concrete task example 2]
- [Concrete task example 3]
- [Concrete task example 4]
- [Concrete task example 5]
- [Concrete task example 6]

**Domain-specific notes:**
- [optimal_build specific guidance 1]
- [Real estate domain consideration]
- [Jurisdiction-specific note (Japan, US, AU)]
- [Technical constraint or preference]
- [Integration consideration]

---

## Template Guidelines

### Structure Requirements

1. **When to engage**: Be specific about triggers. Include:
   - Task types that activate this persona
   - Keywords or patterns to recognize
   - Escalation triggers from other personas

2. **Entry/Exit criteria**: Define clear boundaries:
   - Entry: What must be known or ready before starting
   - Exit: What deliverables or states must be achieved

3. **Do/Anti-patterns**: Be actionable:
   - "Do" items should be specific enough to follow
   - Anti-patterns should describe real mistakes made in past

4. **Collaborates with**: Link to related personas:
   - Show which personas this one hands off to/from
   - Describe the nature of collaboration

5. **Example tasks**: Provide 4-6 concrete examples:
   - Should be recognizable scenarios
   - Mix of simple and complex tasks

6. **Domain-specific notes**: Ground in optimal_build context:
   - Real estate terminology
   - Multi-jurisdiction considerations
   - Technical stack specifics

### Formatting Standards

- Use bullet points, not numbered lists (easier to extend)
- Keep "Do" and "Anti-patterns" to 6-10 items each
- Use bold for persona names in "Collaborates with"
- Include 5+ collaborating personas where possible

### Naming Convention

- File name: `[role_name].md` (snake_case)
- Title: `# Persona: [Role Name]` (Title Case)
- Example: `performance_engineer.md` → `# Persona: Performance Engineer`

### Quality Checklist

Before finalizing a new playbook:

- [ ] All sections present and populated
- [ ] Entry/Exit criteria are measurable
- [ ] At least 5 "Do" items with specific actions
- [ ] At least 4 anti-patterns from real mistakes
- [ ] At least 4 collaborating personas identified
- [ ] At least 4 example tasks provided
- [ ] Domain-specific notes relevant to optimal_build
- [ ] File added to README.md list
- [ ] Corresponding entry exists in MCP.md (Section 2)
