# Optimal Build — User Flow

> Generated: 2026-02-28
> Source: `frontend/src/main.tsx`, `frontend/src/router.tsx`, page-level components

---

## Top-Level Flow

```
App Launch
    │
    └──► / (Business Performance Dashboard)  ◄── default landing
              │
              └──► Top Nav
                      │
                      ├── /projects           → Project List
                      ├── /app/capture        → Unified Capture
                      ├── /cad/upload         → CAD Upload
                      ├── /cad/detection      → CAD Detection
                      ├── /cad/pipelines      → CAD Pipelines
                      ├── /visualizations/intelligence  → Advanced Intelligence
                      ├── /feasibility        → Feasibility Wizard
                      ├── /finance            → Finance Workspace
                      ├── /app/marketing      → Marketing Packs
                      ├── /app/advisory       → Advisory Console
                      └── /app/integrations   → Listing Integrations
```

---

## Flow 1: Project-Centric Workflow

```
/projects
   │
   ├── [Select existing project]
   │        └──► /projects/:id  (Project Hub)
   │                  │
   │                  ├── KPI tiles  (auto-loaded from API)
   │                  └── Module Cards  ──► click to navigate:
   │                            ├── /projects/:id/capture     → Capture
   │                            ├── /projects/:id/feasibility → Feasibility
   │                            ├── /projects/:id/finance     → Finance
   │                            ├── /projects/:id/phases      → Phase Management
   │                            ├── /projects/:id/team        → Team Coordination
   │                            └── /projects/:id/regulatory  → Regulatory
   │
   └── [Create new project]
            └── Dialog: enter name → POST → navigate to /projects/:newId
```

---

## Flow 2: Unified Capture (Property Scan)

```
/app/capture
   │
   ├── PRE-CAPTURE  (full-screen dark Mapbox 3D map)
   │       │
   │       ├── Left Glass Panel (form):
   │       │       ├── Address input  +  [→ geocode] / [← reverse geocode]
   │       │       ├── Latitude / Longitude fields
   │       │       ├── Jurisdiction selector  (SG / HK / NZ / SEA / TOR)
   │       │       ├── Mission Scenarios (multi-select tiles):
   │       │       │       Raw Land │ Existing Building │ Heritage Property
   │       │       │       Underused Asset │ Mixed-Use
   │       │       ├── Developer Mode toggle  (HUD only ↔ Full workspace)
   │       │       └── [Scan & Analyze] button
   │       │
   │       └── Voice Observations Panel  (mic recording, always visible)
   │
   └── POST-CAPTURE  (role-split)
           │
           ├── AGENT MODE  (Developer Mode OFF)
           │       ├── Right panel: Agent Results  (capture summary, market data)
           │       ├── "Enable Developer Mode" CTA
           │       └── Mission Log  (history of captured sites)
           │
           └── DEVELOPER MODE  (Developer Mode ON)
                   ├── Developer workspace section (below map):
                   │       └── DeveloperResults  (Property Overview, 3D Preview,
                   │                              Condition Assessment, Scenario Comparison,
                   │                              Due Diligence Checklist, etc.)
                   └── Mission Log
```

---

## Flow 3: Business Performance (Default Home)

```
/ or /app/performance
   │
   ├── KPI Summary bar:
   │       Last Snapshot │ Open Pipeline Value │ ROI Projects Tracked
   │
   ├── Pipeline Board  (8/12 width)
   │       Kanban columns by deal stage
   │       [Click deal card] ──► loads deal details in sidebar
   │       [Drag / move deal] ──► optimistic stage update via API
   │
   └── Right Sidebar  (4/12 width)
           ├── Deal Insights Panel  (selected deal, timeline, commissions)
           ├── Analytics Panel  (metrics, 30-day trend, benchmarks)
           └── ROI Panel  (automation hours saved, acceptance rate, payback)
```

---

## Flow 4: Finance Workspace

```
/finance  or  /projects/:id/finance
   │
   ├── Project Selector
   ├── Scenario Selector
   │
   ├── Capital Stack  (equity / debt allocation ring + insight box)
   ├── Metrics Grid   (NPV, IRR, yield, etc.)
   ├── Sensitivity Analysis  (controls → table → summary)
   ├── Asset Breakdown
   ├── Facility Editor  (loan terms)
   ├── Loan Interest schedule
   └── Job Timeline  (drawdown header + timeline)
```

---

## Flow 5: Feasibility Wizard

```
/feasibility  or  /projects/:id/feasibility
   │
   ├── Asset Mix View   (unit type allocation)
   ├── Pack Grid        (documentation packs)
   ├── Advisory View    (recommendations)
   └── Clash Impact Board
```

---

## Flow 6: Phase Management

```
/app/phase-management  or  /projects/:id/phases
   │
   ├── Gantt Chart       (project timeline)
   ├── Phase Editor      (add/edit phases)
   └── Tenant Relocation Dashboard
```

---

## Flow 7: Regulatory

```
/app/regulatory  or  /projects/:id/regulatory
   │
   ├── Compliance Path Timeline
   ├── Change of Use Wizard    (step-by-step)
   ├── Heritage Submission Form
   └── Submission Wizard
```

---

## Flow 8: Advisory Console

```
/app/advisory
   │
   ├── Absorption Chart
   ├── Advisory Table
   ├── Asset Mix Panel
   ├── Market Positioning Panel
   └── Feedback Form
```

---

## Role-Based Access Summary

| User Type | Primary Flow | Key Distinction |
|---|---|---|
| **Agent** | Capture → Mission Log → Advisory | HUD-only results, no developer workspace |
| **Developer** | Capture → Full Workspace → Feasibility → Finance | Full workspace, scenario modeling |
| **Developer (project-centric)** | Projects → Hub → Modules | All modules accessible via project context |

The **Developer Mode toggle** on the Capture page is the key branching point — it gates whether agents see the lightweight HUD or the full property analysis workspace.

---

## Full Route Reference

| URL | Page | Notes |
|---|---|---|
| `/` | Business Performance | Default landing (no header/sidebar) |
| `/app/performance` | Business Performance | Alias for `/` |
| `/app/capture` | Unified Capture | Also aliased at `/app/gps-capture`, `/app/site-acquisition` |
| `/app/marketing` | Marketing Packs | |
| `/app/advisory` | Advisory Console | |
| `/app/integrations` | Listing Integrations | PropertyGuru, EdgeProp, Zoho |
| `/app/asset-feasibility` | Feasibility Wizard | |
| `/app/financial-control` | Finance Workspace | |
| `/app/phase-management` | Phase Management | No header/sidebar |
| `/app/team-coordination` | Team Management | No header/sidebar |
| `/app/regulatory` | Regulatory Dashboard | No header/sidebar |
| `/projects` | Project List | |
| `/projects/:id` | Project Hub | KPIs + module cards |
| `/projects/:id/capture` | Unified Capture | Project-scoped |
| `/projects/:id/feasibility` | Feasibility | Project-scoped |
| `/projects/:id/finance` | Finance | Project-scoped |
| `/projects/:id/phases` | Phase Management | Project-scoped |
| `/projects/:id/team` | Team Management | Project-scoped |
| `/projects/:id/regulatory` | Regulatory | Project-scoped |
| `/cad/upload` | CAD Upload | |
| `/cad/detection` | CAD Detection | |
| `/cad/pipelines` | CAD Pipelines | |
| `/visualizations/intelligence` | Advanced Intelligence | |
| `/developer` | Developer Control Panel | Internal tooling |
| `/agents/developers/:id/preview` | Developer Preview | Standalone QA viewer |
| `/app/site-acquisition/checklist-templates` | Checklist Template Manager | |
