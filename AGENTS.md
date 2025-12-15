# AI Agents Guide

Welcome to the **optimal_build** AI team. This codebase is maintained by a collaboration of human and artificial intelligence.

## Interaction Protocol

When working with AI agents in this repository, you should be aware of the "Persona" system defined in **[MCP.md](./MCP.md)**.

For extended persona playbooks, see **[docs/ai-agents/](./docs/ai-agents/)**.

### How to direct an Agent

You can explicitly ask an agent to adopt a persona to get better results:

-   **"Act as the Architect"**: Use this when you need to discuss system design, folder structure, or integration patterns.
    -   _Expect_: High-level diagrams, trade-off analysis, "Clean Architecture" references.
-   **"Act as the QA Engineer"**: Use this when you need test plans, edge case analysis, or help fixing a stubborn bug.
    -   _Expect_: `pytest` commands, corner case identification, "breaking" inputs.
-   **"Act as the UI/UX Designer"**: Use this when refining the frontend.
    -   _Expect_: CSS adjustments, accessibility checks, user flow improvements.

### The Constitution

All agents are bound by the Core Directives in `MCP.md`. They are instructed to prioritize:

1.  **Quality** (No broken code)
2.  **Testing** (Mandatory verification)
3.  **Security** (Paranoid validation)

## Agent Roster

| Agent Type | File        | Primary Function                                         |
| :--------- | :---------- | :------------------------------------------------------- |
| **Claude** | `CLAUDE.md` | General purpose coding, implementation, and refactoring. |
| **Gemini** | `GEMINI.md` | Large-context analysis, complex synthesis, and planning. |

_Note: All agents share the same brain (`MCP.md`)._
