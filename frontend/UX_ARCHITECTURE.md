# UX Architecture & Design Patterns

> **CRITICAL**: AI agents MUST read this document before implementing UI layouts and patterns.
> For design token VALUES (spacing, colors, radius), see [UI_STANDARDS.md](./UI_STANDARDS.md).

This document defines **when, why, and how** to use design patterns. It complements UI_STANDARDS.md which defines **what values** to use.

---

## Document Map

| Document                           | Purpose                                            | When to Read                  |
| ---------------------------------- | -------------------------------------------------- | ----------------------------- |
| **UI_STANDARDS.md**                | Token values (spacing, radius, colors, typography) | When writing CSS/styling      |
| **UX_ARCHITECTURE.md** (this file) | Layout patterns, decision trees, principles        | When designing page structure |
| **STYLE_GUIDE.md**                 | CSS class architecture, BEM naming                 | When adding new CSS classes   |

---

## AI Studio Design Principles (MANDATORY)

These 6 principles govern all UI/UX decisions in this project. Follow them in order of priority.

### 1. Information Density vs Visual Noise

**Goal:** Maximize data shown per viewport while maintaining strict visual hierarchy.

**Implementation:**

- Use typography weight and size to create clear hierarchy (not boxes around everything)
- Apply the "Content vs Context" separation (see Section below)
- Reserve card surfaces for actionable data; contextual labels go on background
- Avoid "nesting fatigue" (cards inside cards)

**Signals of Violation:**

- Multiple nested borders/shadows competing for attention
- Headers wrapped in cards that also contain cards
- Low information density (< 3 data points visible above the fold)

### 2. Responsive Resilience

**Goal:** Layouts adapt gracefully from 320px to 2560px without breaking.

**Implementation:**

- Use fluid Grid layouts with proper breakpoint ratios (`xs={12} lg={8}`)
- Apply viewport-aware height constraints (`100vh - header`)
- Header areas should compact on mobile (reduce padding, smaller typography)
- Use tabs or accordions instead of stacking sections vertically

**Signals of Violation:**

- Horizontal scrolling at any viewport
- Content clipping on small screens
- Pages exceeding 2 viewport heights on desktop

### 3. Functional Color Language

**Goal:** Colors communicate function instantly without requiring user learning.

**Implementation:**

- **Cyan** (`#00f3ff`): Brand/selection (active tabs, primary CTA, logo)
- **Green** (success.main): Vitality/success (live, active, positive trends)
- **Red** (error.main): Errors/critical (failed, delete, negative)
- **Amber** (warning.main): Caution/attention (offline, critical path, warnings)
- **Indigo** (info.main): Categories/AI (data differentiation, intelligence indicators)
- **Slate/Gray**: Neutral hierarchy (primary/secondary/tertiary text)

**Decision Tree:** See "Text Color Decision Tree" section below.

**Signals of Violation:**

- Using cyan for error or success states
- Using green for non-success states
- Hardcoded hex colors instead of semantic tokens

### 4. Progressive Disclosure

**Goal:** AI insights and complex details are available on-demand, not overwhelming by default.

**Implementation:**

- Primary data visible immediately
- AI-generated insights behind toggle buttons or expandable sections
- Use "Show more" patterns for verbose content
- Tooltips for secondary information

**Signals of Violation:**

- AI insight paragraphs always visible
- 500+ word text blocks visible by default
- No way to collapse complex details

### 5. Technical Authority Branding

**Goal:** Interface feels like a mission control system, not a consumer app.

**Implementation:**

- Breadcrumbs and location indicators visible
- Status bars with system health information
- Monospace fonts for technical data
- Sharp corners (2-8px max) not rounded
- Glassmorphism with neon accents

**Signals of Violation:**

- Rounded corners > 8px
- Consumer-app aesthetic (bubbly, colorful, playful)
- Missing location/breadcrumb context

### 6. Summary Footer Pattern

**Goal:** Aggregate statistics persist at the bottom of data-heavy sections.

**Implementation:**

- Footer bar with key aggregate metrics (totals, averages, counts)
- Sticky or fixed position when scrolling
- High contrast for quick scanning
- 3-5 key metrics maximum

**Signals of Violation:**

- No visible summary when viewing data tables
- Aggregates only at top (user must scroll back up)
- More than 6 metrics in footer (information overload)

---

## Content vs Context Separation

This is the foundational layout principle for data-heavy pages.

### The Core Concept

| Element Type            | Placement    | Purpose                             |
| ----------------------- | ------------ | ----------------------------------- |
| **Contextual metadata** | Background   | Tells you WHAT you're looking at    |
| **Section headers**     | Background   | Names the section or entity         |
| **Descriptions**        | Background   | Provides context before data        |
| **Actionable content**  | Card surface | Tables, forms, interactive elements |
| **Data entities**       | Card surface | Modular, comparable units           |

### Visual Comparison

```
❌ WRONG: Cards inside cards (nesting fatigue)
┌─────────────────────────────────┐
│ Section Card                    │
│  ┌───────────────────────────┐  │
│  │ Data Card                 │  │
│  │  • Row 1                  │  │
│  │  • Row 2                  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘

✅ CORRECT: Section header on background, only data in card
Section Header (on background)
Description text (on background)
┌───────────────────────────────┐
│ Data Card                     │
│  • Row 1                      │
│  • Row 2                      │
└───────────────────────────────┘
```

### Why This Works

1. **Information Hierarchy**: Typography weight creates hierarchy without extra borders
2. **Visual Breathability**: Negative space separates sections naturally
3. **Maximum Data Width**: No wrapper padding stealing horizontal space
4. **Scalability**: Adding new sections is simple (just another header + card)

### Implementation Pattern

```tsx
// Authority/Entity section with data table
<Box sx={{ mb: 'var(--ob-space-300)' }}>
    {/* Header on background */}
    <Stack
        direction="row"
        alignItems="center"
        gap="var(--ob-space-100)"
        mb="var(--ob-space-050)"
    >
        <Box className="ob-status-dot ob-status-dot--live" />
        <Typography variant="h6" fontWeight={700}>
            BCA
        </Typography>
    </Stack>

    {/* Description on background */}
    <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mb: 'var(--ob-space-200)' }}
    >
        Building & Construction Authority: Safety, Fire, & Accessibility
    </Typography>

    {/* Data in card */}
    <Box className="ob-card-module">
        <RulesTable rules={bcaRules} />
    </Box>
</Box>
```

---

## Text Color Decision Tree (MANDATORY)

When choosing a text color, follow this decision tree:

```
Is this text showing a STATUS or STATE?
├─ YES → Use semantic colors:
│        • Active/Live/Success → Green (success.main)
│        • Error/Failed/Critical Alert → Red (error.main)
│        • Warning/Attention/Critical Path → Amber (warning.main)
│        • Informational category → Indigo (info.main)
│
└─ NO → Is this text part of a BRAND element or ACTIVE selection?
        ├─ YES → Use Cyan (var(--ob-color-neon-cyan))
        │        • Brand name, logo text
        │        • Active tab/selection indicator
        │        • Primary CTA button text
        │
        └─ NO → Use grayscale hierarchy:
                • Primary content → var(--ob-text-primary)
                • Descriptions/secondary → var(--ob-text-secondary)
                • Labels/captions/meta → var(--ob-text-tertiary)
                • Disabled/placeholder → var(--ob-text-disabled)
```

### Key Rules

1. **Status text must use semantic colors** - Never use indigo/cyan for success, error, or warning states
2. **Critical/Important items use amber** - "CRITICAL" labels, critical path indicators, attention-needed states
3. **Indigo is for categorization and AI intelligence only** - Not for emphasis or importance
4. **Cyan is for brand/selection only** - Not for semantic meaning
5. **Default to grayscale** - When in doubt, use the text hierarchy

---

## Card Surface Decision Tree

Use this to determine if content needs a card wrapper:

```
Is this content a GROUPED collection of related items?
├─ YES (metrics grid, data table, form section, rule list)
│   └─ Use card surface → GlassCard or .ob-card-module
│
└─ NO → Is this content INTERACTIVE (form controls, selectors)?
        ├─ YES → Check parent context:
        │        • Parent has .ob-card-module? → Use variant="embedded"
        │        • No parent surface? → Wrap in GlassCard
        │
        └─ NO → Is this a VISUALIZATION (chart, diagram)?
                ├─ YES → Wrap in GlassCard for containment
                │
                └─ NO → Is this a PAGE-LEVEL element (header, banner)?
                        ├─ YES → Place directly on background (no card)
                        └─ NO → Default to GlassCard for visual grouping
```

### Card Surface Standards

| Content Type        | Surface                    | Example                                   |
| ------------------- | -------------------------- | ----------------------------------------- |
| Metrics grid        | `GlassCard`                | KPI cards, summary stats                  |
| Data table          | `GlassCard` with overflow  | User lists, transaction logs              |
| Form section        | `.ob-card-module`          | Settings panel, upload form               |
| Chart/visualization | `GlassCard`                | Bar charts, line graphs                   |
| Page header         | No surface (on background) | Title, breadcrumbs, page actions          |
| Error/alert banners | No surface (on background) | Placed OUTSIDE cards                      |
| Embedded components | `variant="embedded"`       | Child components inside `.ob-card-module` |

### Avoiding Nested Surfaces

**NEVER** nest card surfaces:

```tsx
// ❌ WRONG - Double surface
<Box className="ob-card-module">
  <GlassCard>           {/* Creates nested surface! */}
    <MyComponent />
  </GlassCard>
</Box>

// ✅ CORRECT - Single surface with embedded variant
<Box className="ob-card-module">
  <MyComponent variant="embedded" />  {/* No inner surface */}
</Box>
```

---

## Layout Patterns

### Master-Detail Layout (2:1 Grid)

For pages with primary content + selection/control panel.

**Use Cases:** Finance scenarios, CAD configurations, project comparisons, analytics dashboards.

| Column         | Width            | Content                               |
| -------------- | ---------------- | ------------------------------------- |
| Left (Master)  | `xs={12} lg={8}` | Chart, visualization, primary content |
| Right (Detail) | `xs={12} lg={4}` | Scenario selector, controls, filters  |

```tsx
<Grid container spacing="var(--ob-space-150)">
    {/* Master: Chart/Visualization (2/3 width on lg+) */}
    <Grid item xs={12} lg={8}>
        <GlassCard sx={{ p: 'var(--ob-space-100)' }}>
            <ChartComponent scenarios={scenarios} />
        </GlassCard>
    </Grid>

    {/* Detail: Scenario Selector (1/3 width on lg+) */}
    <Grid item xs={12} lg={4}>
        <ScenarioCards
            scenarios={scenarios}
            activeId={activeId}
            onSelect={handleSelect}
        />
    </Grid>
</Grid>
```

### Selection Card List Pattern

Vertical list of clickable cards for switching between items.

**Use Cases:** Scenario selectors, configuration profiles, project lists, template pickers.

| State                | Styling                                                                             |
| -------------------- | ----------------------------------------------------------------------------------- |
| **Default**          | `bgcolor: 'background.paper'`, `border: 1`, `borderColor: 'divider'`                |
| **Hover**            | `borderColor: 'primary.main'`, `boxShadow: 2`                                       |
| **Active**           | `bgcolor: alpha(primary, 0.05)`, `borderColor: alpha(primary, 0.3)`, `boxShadow: 1` |
| **Active Indicator** | `8px` dot with `borderRadius: '50%'`, `bgcolor: 'primary.main'`                     |

### Underlined Tab Navigation Pattern

For secondary/tertiary navigation within a page section.

**Use Cases:** Sub-navigation within panels, switching between related views, filtering content.

| Element        | Styling                                                                    |
| -------------- | -------------------------------------------------------------------------- |
| Container      | `borderBottom: 1, borderColor: 'divider'`                                  |
| Tab (inactive) | `borderBottom: 2`, `borderColor: 'transparent'`, `color: 'text.secondary'` |
| Tab (active)   | `borderBottom: 2`, `borderColor: 'primary.main'`, `color: 'primary.main'`  |
| Tab (hover)    | `color: 'text.primary'`, `bgcolor: 'transparent'`                          |

### Workspace Page Pattern

For complex workspace pages (Finance, CAD, Feasibility):

```tsx
<AppLayout title="Finance" subtitle="Scenario modeling">
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Toolbar - fixed */}
        <Card sx={{ flexShrink: 0, mb: 2 }}>
            <Toolbar />
        </Card>

        {/* Tabs - fixed */}
        <Tabs value={tab} sx={{ flexShrink: 0 }} />

        {/* Tab content - fills remaining space */}
        <Box sx={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
            <TabPanel>{activeContent}</TabPanel>
        </Box>
    </Box>
</AppLayout>
```

---

## Data Table Pattern

For professional data tables with type/status badges and styled headers.

**Use Cases:** Financial tables, inventory lists, user management, audit logs.

### Table Structure

| Element           | Styling                                                                         |
| ----------------- | ------------------------------------------------------------------------------- |
| Card wrapper      | `GlassCard sx={{ overflow: 'hidden' }}`                                         |
| Header row        | `bgcolor: alpha(background.default, 0.5)`                                       |
| Column headers    | `textTransform: 'uppercase'`, `letterSpacing: 'var(--ob-letter-spacing-wider)'` |
| Numeric columns   | `textAlign: 'right'`, `fontFamily: 'var(--ob-font-family-mono)'`                |
| Status/Type badge | `StatusChip` with appropriate status color                                      |
| Summary/Total row | `bgcolor: alpha(background.default, 0.5)`, `fontWeight: 600`                    |
| Row hover         | `bgcolor: alpha(action.hover, 0.5)`                                             |

### Status Badge Guidelines

| Category        | StatusChip Props           | Example Use                             |
| --------------- | -------------------------- | --------------------------------------- |
| Positive/Active | `status="success"` (green) | Approved, Active, Complete, Equity      |
| Informational   | `status="info"` (indigo)   | Pending, In Progress, Primary, Debt     |
| Caution         | `status="warning"` (amber) | Review Needed, Expiring Soon, Mezzanine |
| Negative/Error  | `status="error"` (red)     | Failed, Rejected, Overdue               |
| Neutral         | `status="default"` (gray)  | Draft, Archived, N/A                    |

---

## Insight/Callout Box Pattern

For displaying AI-generated insights with colored callout styling.

**Use Cases:** AI recommendations, analysis summaries, important notices, validation feedback.

### Visual Variants

| Variant | Background                  | Border                     | Text Color     | When to Use                      |
| ------- | --------------------------- | -------------------------- | -------------- | -------------------------------- |
| Success | `alpha(success.main, 0.08)` | `alpha(success.main, 0.3)` | `success.dark` | Positive insights, confirmations |
| Info    | `alpha(primary.main, 0.08)` | `alpha(primary.main, 0.3)` | `primary.dark` | Neutral information, tips        |
| Warning | `alpha(warning.main, 0.08)` | `alpha(warning.main, 0.3)` | `warning.dark` | Caution, attention needed        |
| Error   | `alpha(error.main, 0.08)`   | `alpha(error.main, 0.3)`   | `error.dark`   | Critical issues, failures        |

### Common Header Labels

| Label    | Use For                                  |
| -------- | ---------------------------------------- |
| ANALYSIS | AI-generated insights, data analysis     |
| TIP      | Helpful suggestions, best practices      |
| NOTE     | Additional context, clarifications       |
| WARNING  | Caution messages, potential issues       |
| SUCCESS  | Confirmation messages, completed actions |
| ERROR    | Failure messages, validation errors      |

---

## Metrics Grid Pattern

For displaying KPIs, financial metrics, or summary statistics.

### Layout

- 4-column grid on desktop: `xs={6} md={3}`
- 2-column grid on mobile
- Spacing: `spacing="var(--ob-space-100)"` between cards

### Metric Card Structure

| Element   | Standard                                                        |
| --------- | --------------------------------------------------------------- |
| Container | `GlassCard` with `p: 'var(--ob-space-100)'`                     |
| Label     | `fontSize: 'var(--ob-font-size-sm)'`, `color: 'text.secondary'` |
| Value     | `fontSize: 'var(--ob-font-size-2xl)'`, `fontWeight: 700`        |

---

## Chart & Visualization Guidelines

### Chart Library Requirements

| Requirement | Standard                                | Rationale                       |
| ----------- | --------------------------------------- | ------------------------------- |
| Library     | **Recharts** only                       | Already installed, React-native |
| Container   | Wrap in `ResponsiveContainer`           | Ensures responsive behavior     |
| Height      | Use `--ob-max-height-panel` (400px) max | Prevents viewport overflow      |
| Colors      | Use theme palette via `useTheme()`      | Dark mode compatible            |
| Labels      | Use i18n `t()` function                 | Internationalization            |

### Chart Styling Requirements

| Element         | Standard                               | Token/Value               |
| --------------- | -------------------------------------- | ------------------------- |
| Bar corners     | Use radius `4`                         | Matches `--ob-radius-sm`  |
| Tooltip corners | Use radius `4`                         | Matches `--ob-radius-sm`  |
| Grid lines      | `vertical={false}`, stroke from theme  | Clean, minimal appearance |
| Axis lines      | `axisLine={false}`, `tickLine={false}` | Modern, minimal style     |
| Axis text       | `fontSize: 12`, `fill` from theme      | Use `text.secondary`      |

### Chart Type Selection

| Use Case           | Chart Type     | Recharts Component            |
| ------------------ | -------------- | ----------------------------- |
| Compare categories | Stacked Bar    | `BarChart` with `stackId`     |
| Timeline with mix  | Composed       | `ComposedChart` (Bar + Line)  |
| Part of whole      | Donut/Pie      | `PieChart` with `innerRadius` |
| Trend over time    | Line           | `LineChart` or `AreaChart`    |
| Distribution       | Horizontal Bar | `BarChart layout="vertical"`  |

---

## Viewport & Layout Standards

### Height Constraints

| Constraint                   | Value           | Use Cases                              |
| ---------------------------- | --------------- | -------------------------------------- |
| `--ob-max-height-panel`      | 400px           | Scrollable panels within a page        |
| `--ob-max-height-table`      | 500px           | Data tables with internal scroll       |
| `--ob-max-height-card-group` | 600px           | Grouped cards with overflow scroll     |
| `100vh - header`             | calc(100vh - X) | Full-height layouts minus fixed header |

### Layout DO's and DON'Ts

**DO:**

- Use `height: 100%` or `flex: 1` with overflow containers
- Use tabs, accordions, or collapsible sections for multi-section content
- Use `maxHeight` with `overflow: auto` for scrollable content areas
- Use grid layouts that adapt to available space

**DON'T:**

- Stack more than 3-4 major sections vertically without grouping
- Render all content at once if it exceeds ~2 viewport heights
- Use fixed heights that cause content clipping on small screens
- Render 100+ items without virtualization or pagination

---

## Architecture Checklist

Before submitting UI code changes, verify:

**Layout & Viewport:**

- [ ] Page fits within ~2 viewport heights maximum
- [ ] Multi-section content uses tabs or accordions (NOT vertical stacking)
- [ ] Data tables have `maxHeight` with internal scroll
- [ ] Workspace pages follow fixed-toolbar + tabs + scrollable-content pattern
- [ ] Large lists use virtualization or pagination

**Content vs Context:**

- [ ] Section headers are on background (not wrapped in cards)
- [ ] Descriptions are on background (not inside data cards)
- [ ] Only actionable content is in card surfaces
- [ ] No nested card surfaces (cards inside cards)

**Color Usage (follow decision tree):**

- [ ] Status/state text uses semantic colors (green/red/amber/indigo)
- [ ] Critical/attention items use amber, NOT indigo
- [ ] Brand elements and active selections use cyan
- [ ] Descriptions use grayscale hierarchy
- [ ] Indigo is only for category differentiation and AI intelligence

**Layout Patterns:**

- [ ] Master-Detail layouts use Grid `xs={12} lg={8}` / `xs={12} lg={4}` split
- [ ] Selection card lists have proper active state styling
- [ ] Data tables use GlassCard wrapper with styled header row
- [ ] Status badges use StatusChip with appropriate status colors
- [ ] Summary/footer rows have gray background

**Charts & Visualizations:**

- [ ] Using Recharts (not other chart libraries)
- [ ] Chart wrapped in `ResponsiveContainer`
- [ ] Chart height ≤ `--ob-max-height-panel` (400px)
- [ ] Colors from theme palette (not hardcoded hex)
- [ ] Chart labels use i18n `t()` function

---

## Reference Implementations

- **Content vs Context**: [RulePackExplanationPanel.tsx](src/modules/cad/RulePackExplanationPanel.tsx)
- **AI Studio Principles**: [MultiScenarioComparisonSection.tsx](src/app/pages/site-acquisition/components/multi-scenario-comparison/MultiScenarioComparisonSection.tsx)
- **Master-Detail Layout**: [FinanceWorkspace.tsx](src/modules/finance/FinanceWorkspace.tsx)
