# UI Design Standards for AI Agents

> **CRITICAL**: AI agents MUST follow these standards when writing or modifying UI code.
> This document is the source of truth for design token usage.

## Design Philosophy: Square Cyber-Minimalism

This project uses a **Square Cyber-Minimalism** aesthetic with sharp, minimal border-radii.
All UI elements should feel clean, technical, and modern - NOT rounded or "soft".

---

## Border Radius Standards (MANDATORY)

| Token              | Value  | Use Cases                                 | NEVER Use For  |
| ------------------ | ------ | ----------------------------------------- | -------------- |
| `--ob-radius-none` | 0px    | Tables, data grids                        | -              |
| `--ob-radius-xs`   | 2px    | Buttons, tags, chips, badges              | Cards, modals  |
| `--ob-radius-sm`   | 4px    | Cards, panels, tiles, inputs              | Avatars, pills |
| `--ob-radius-md`   | 6px    | Inputs, select boxes, dropdowns           | -              |
| `--ob-radius-lg`   | 8px    | Modals, dialogs, windows ONLY             | Cards, buttons |
| `--ob-radius-pill` | 9999px | Avatars, circular icons, pill badges ONLY | Cards, panels  |

### Examples

```tsx
// ✅ CORRECT - Card with 4px radius
<GlassCard sx={{ borderRadius: 'var(--ob-radius-sm)' }}>

// ❌ WRONG - Hardcoded value
<GlassCard sx={{ borderRadius: 4 }}>  // MUI multiplies by 8 = 32px!

// ❌ WRONG - Using lg for a card
<GlassCard sx={{ borderRadius: 'var(--ob-radius-lg)' }}>  // lg is for modals only

// ✅ CORRECT - Button with 2px radius
<Button sx={{ borderRadius: 'var(--ob-radius-xs)' }}>

// ✅ CORRECT - Modal with 8px radius
<Dialog PaperProps={{ sx: { borderRadius: 'var(--ob-radius-lg)' } }}>
```

---

## Spacing Standards (MANDATORY)

NEVER use hardcoded pixel/rem values. Prefer design tokens.
If you use MUI numeric spacing (e.g. `spacing={2}` or `sx={{ p: 2 }}`), it MUST remain token-based via the app theme's `theme.spacing()` mapping (so you still get tokenized spacing, not arbitrary pixels).

| Token            | Value | Use Cases                          |
| ---------------- | ----- | ---------------------------------- |
| `--ob-space-025` | 4px   | Micro adjustments                  |
| `--ob-space-050` | 8px   | Tight spacing, icon gaps           |
| `--ob-space-075` | 12px  | Medium-tight spacing               |
| `--ob-space-100` | 16px  | Default component padding          |
| `--ob-space-150` | 24px  | Standard gaps, section spacing     |
| `--ob-space-200` | 32px  | Large gaps, page sections          |
| `--ob-space-250` | 40px  | Large section dividers             |
| `--ob-space-300` | 48px  | Major sections                     |
| `--ob-space-400` | 64px  | Page-level spacing                 |
| `--ob-space-500` | 40px  | Back-compat alias (maps to `-250`) |
| `--ob-space-600` | 48px  | Back-compat alias (maps to `-300`) |
| `--ob-space-800` | 64px  | Back-compat alias (maps to `-400`) |

### Examples

```tsx
// ✅ CORRECT - Token-based spacing
<Stack spacing="var(--ob-space-100)">
<Box sx={{ p: 'var(--ob-space-150)', gap: 'var(--ob-space-050)' }}>

// ✅ ALSO OK - tokenized MUI spacing numbers (mapped via theme.spacing)
<Stack spacing={2}>
<Box sx={{ p: 3, gap: 1 }}>

// ❌ WRONG - Hardcoded values
<Box sx={{ p: '24px' }}>   // Hardcoded px
<Box sx={{ gap: 16 }}>     // Hardcoded number
```

---

## Size Standards (MANDATORY)

| Token                    | Value  | Use Cases                  |
| ------------------------ | ------ | -------------------------- |
| `--ob-size-icon-sm`      | 24px   | Small icons                |
| `--ob-size-icon-md`      | 32px   | Default icons              |
| `--ob-size-icon-lg`      | 48px   | Large icons, avatars       |
| `--ob-size-icon-xl`      | 64px   | Hero icons                 |
| `--ob-size-drop-zone`    | 120px  | File drop zones min-height |
| `--ob-size-controls-min` | 400px  | Control bars min-width     |
| `--ob-max-width-content` | 1000px | Content max-width          |
| `--ob-max-width-page`    | 1400px | Page max-width             |

### Examples

```tsx
// ✅ CORRECT
<Box sx={{ width: 'var(--ob-size-icon-lg)', height: 'var(--ob-size-icon-lg)' }}>
<Box sx={{ maxWidth: 'var(--ob-max-width-content)' }}>

// ❌ WRONG
<Box sx={{ width: 48, height: 48 }}>
<Box sx={{ maxWidth: '1000px' }}>
```

---

## Typography Standards (MANDATORY)

| Token                     | Value     | Use Cases                             |
| ------------------------- | --------- | ------------------------------------- |
| `--ob-font-size-2xs`      | 0.6875rem | Smallest readable, timestamps, badges |
| `--ob-font-size-xs`       | 0.75rem   | Captions, labels, meta text           |
| `--ob-font-size-sm-minus` | 0.8125rem | Small body text, compact UI           |
| `--ob-font-size-sm`       | 0.875rem  | Secondary text, descriptions          |
| `--ob-font-size-md`       | 0.9375rem | Enhanced body text                    |
| `--ob-font-size-base`     | 1rem      | Primary body text                     |
| `--ob-font-size-lg`       | 1.125rem  | Section headings, lead text           |
| `--ob-font-size-xl`       | 1.25rem   | Page subtitles                        |
| `--ob-font-size-2xl`      | 1.5rem    | Page titles                           |
| `--ob-font-size-3xl`      | 1.875rem  | Hero headings                         |
| `--ob-font-size-4xl`      | 2.25rem   | Display headings                      |
| `--ob-font-size-5xl`      | 3rem      | Large display                         |

### Examples

```tsx
// ✅ CORRECT
<Typography sx={{ fontSize: 'var(--ob-font-size-xs)' }}>

// ❌ WRONG
<Typography sx={{ fontSize: '12px' }}>
<Typography sx={{ fontSize: 12 }}>
```

---

## Blur/Backdrop Standards

| Token          | Value | Use Cases             |
| -------------- | ----- | --------------------- |
| `--ob-blur-sm` | 4px   | Subtle blur           |
| `--ob-blur-xs` | 8px   | Light glass surfaces  |
| `--ob-blur-md` | 12px  | Standard glass effect |
| `--ob-blur-xl` | 16px  | Strong glass surfaces |
| `--ob-blur-lg` | 24px  | Heavy blur            |

### Examples

```tsx
// ✅ CORRECT
<Box sx={{ backdropFilter: 'blur(var(--ob-blur-md))' }}>

// ❌ WRONG
<Box sx={{ backdropFilter: 'blur(12px)' }}>
```

---

## Z-Index Standards

| Token                   | Value | Use Cases             |
| ----------------------- | ----- | --------------------- |
| `--ob-z-base`           | 0     | Default               |
| `--ob-z-dropdown`       | 1000  | Dropdowns             |
| `--ob-z-sticky`         | 1020  | Sticky headers        |
| `--ob-z-fixed`          | 1030  | Fixed headers/footers |
| `--ob-z-modal-backdrop` | 1040  | Modal backdrop        |
| `--ob-z-modal`          | 1050  | Modals                |
| `--ob-z-popover`        | 1060  | Popovers              |
| `--ob-z-tooltip`        | 1070  | Tooltips              |

---

## Color Standards

NEVER use hardcoded hex colors. Use:

- MUI theme colors: `theme.palette.primary.main`, `text.primary`, `background.paper`
- Design tokens for brand colors: `var(--ob-brand-500)`, `var(--ob-success-500)`
- Semantic tokens: `var(--ob-color-border-subtle)`, `var(--ob-error-muted)`

---

## Premium Cyber Color System (MANDATORY)

This project uses a **"Mission Control" aesthetic** with Cyan (`#00f3ff`) as the primary brand color and semantic colors for functional meaning. Understanding when to use each color is critical.

### Primary Color: Neon Cyan (`#00f3ff`)

**Token:** `var(--ob-color-neon-cyan)`

**Use For:**

- Brand elements (logo, app name)
- Active/selected states (tabs, cards, navigation items)
- Primary data visualization (chart lines, active bars)
- Primary action buttons
- Selection indicators (active dots, underlines)
- Key metric values that need emphasis

**Examples:**

```tsx
// ✅ CORRECT - Cyan for active tab
borderColor: isActive ? 'var(--ob-color-neon-cyan)' : 'transparent'
color: isActive ? 'var(--ob-color-neon-cyan)' : 'text.secondary'

// ✅ CORRECT - Cyan for primary button
background: 'linear-gradient(135deg, #0096cc 0%, var(--ob-color-neon-cyan) 100%)'

// ✅ CORRECT - Cyan for brand text
<Typography sx={{ color: 'var(--ob-color-neon-cyan)', textShadow: 'var(--ob-glow-neon-text)' }}>
  OPTIMAL BUILD
</Typography>
```

### Semantic Colors (For Functional Meaning)

These colors provide **instant functional meaning** and should NOT be replaced with cyan:

#### 1. Green (Emerald-500/400) — Success & Vitality

**Tokens:** `success.main`, `var(--ob-success-500)`, `var(--ob-color-status-success-text)`

**Use For:**

- "System Live" / "Active" status indicators
- Positive performance trends (+4.2% ROI)
- Success confirmations ("Saved", "Approved")
- Healthy/operational states
- "Go" signals

```tsx
// ✅ CORRECT - Green for success status
<StatusChip status="success">Active</StatusChip>
<StatusChip status="success" pulse>System Live</StatusChip>

// ✅ CORRECT - Green for positive trend
<Typography sx={{ color: 'success.main' }}>+4.2%</Typography>
```

#### 2. Red/Rose (Rose-500/400) — Errors & Critical Alerts

**Tokens:** `error.main`, `var(--ob-error-500)`, `var(--ob-color-status-error-text)`

**Use For:**

- Failed pipeline jobs
- Error messages
- "Remove" / "Delete" actions
- Critical alerts that need immediate attention
- Validation failures

```tsx
// ✅ CORRECT - Red for error status
<StatusChip status="error">Failed</StatusChip>

// ✅ CORRECT - Red for delete button
<IconButton color="error" onClick={handleDelete}>
  <DeleteIcon />
</IconButton>
```

#### 3. Orange/Amber (Amber-500) — Warnings & Significance

**Tokens:** `warning.main`, `var(--ob-warning-500)`, `var(--ob-color-status-warning-text)`

**Use For:**

- "Offline Mode" banners
- "Critical Path" in Gantt charts
- Bottlenecks or states requiring awareness
- Caution messages (not emergencies)
- "Attention needed" indicators

```tsx
// ✅ CORRECT - Amber for warning
<StatusChip status="warning">Offline Mode</StatusChip>
<Alert severity="warning">Critical Path: Permit approval</Alert>
```

#### 4. Blue (Blue-500) — Secondary Information

**Tokens:** `info.main`, `var(--ob-info-500)`, `var(--ob-brand-500)`

**Use For:**

- Differentiating data categories (Office vs Retail)
- Secondary information in charts
- Team roles differentiation
- Informational notices (not action-required)

```tsx
// ✅ CORRECT - Blue for category differentiation
<StatusChip status="info">Office</StatusChip>
<StatusChip status="info">Consultant</StatusChip>
```

### Color Decision Matrix

| Scenario                  | Color         | Token/Value                 |
| ------------------------- | ------------- | --------------------------- |
| Active tab/selection      | Cyan          | `var(--ob-color-neon-cyan)` |
| Brand name/logo           | Cyan          | `var(--ob-color-neon-cyan)` |
| Primary CTA button        | Cyan gradient | See Button component        |
| Chart primary data        | Cyan          | `#00f3ff`                   |
| "Active" / "Live" status  | Green         | `status="success"`          |
| Positive metrics (+%)     | Green         | `success.main`              |
| "Failed" / "Error" status | Red           | `status="error"`            |
| Delete/Remove actions     | Red           | `error.main`                |
| "Offline" / "Warning"     | Amber         | `status="warning"`          |
| Critical path indicator   | Amber         | `warning.main`              |
| Category differentiation  | Blue          | `status="info"`             |
| Neutral/Draft status      | Gray          | `status="neutral"`          |

### Glassmorphism & Glow Effects

All semantic colors should use **low-opacity backgrounds and neon borders** to maintain the premium glassmorphism aesthetic:

```tsx
// ✅ CORRECT - Semantic color with glassmorphism
<Box sx={{
  bgcolor: 'rgba(0, 255, 157, 0.08)',  // Success with low opacity
  border: '1px solid rgba(0, 255, 157, 0.3)',
  borderRadius: 'var(--ob-radius-sm)',
}}>

// StatusChip handles this automatically via status prop
<StatusChip status="success">Active</StatusChip>  // Uses correct opacity
```

### What NOT to Do

```tsx
// ❌ WRONG - Replacing semantic green with cyan for status
<StatusChip status="live">Active</StatusChip>  // "Active" should be green!

// ❌ WRONG - Using cyan for error state
<Typography sx={{ color: 'var(--ob-color-neon-cyan)' }}>Failed</Typography>

// ❌ WRONG - Using hardcoded colors
<Box sx={{ bgcolor: '#22c55e' }}>  // Use theme tokens!

// ❌ WRONG - Using full opacity semantic colors (breaks glassmorphism)
<Box sx={{ bgcolor: 'success.main' }}>  // Should use alpha!
```

---

## Canonical Components

Always prefer canonical components from `src/components/canonical/`:

| Component     | Use Instead Of                   |
| ------------- | -------------------------------- |
| `GlassCard`   | MUI Paper, Card                  |
| `GlassButton` | MUI Button (for glass effect)    |
| `StatusChip`  | MUI Chip (for status indicators) |
| `Input`       | MUI TextField                    |
| `HeroMetric`  | Custom metric displays           |

---

## Viewport & Layout Standards (MANDATORY)

Pages should fit within a single viewport or use progressive disclosure to prevent excessive scrolling.

### Height Constraints

| Constraint                   | Value           | Use Cases                              |
| ---------------------------- | --------------- | -------------------------------------- |
| `--ob-max-height-panel`      | 400px           | Scrollable panels within a page        |
| `--ob-max-height-table`      | 500px           | Data tables with internal scroll       |
| `--ob-max-height-card-group` | 600px           | Grouped cards with overflow scroll     |
| `100vh - header`             | calc(100vh - X) | Full-height layouts minus fixed header |

### Layout Patterns

**DO: Use viewport-aware layouts**

- Use `height: 100%` or `flex: 1` with overflow containers
- Use tabs, accordions, or collapsible sections for multi-section content
- Use `maxHeight` with `overflow: auto` for scrollable content areas
- Use grid layouts that adapt to available space

**DON'T: Create infinitely tall pages**

- Don't stack more than 3-4 major sections vertically without grouping
- Don't render all content at once if it exceeds ~2 viewport heights
- Don't use fixed heights that cause content clipping on small screens

### Page Layout Guidelines

1. **Single-purpose pages**: Fit primary content in one viewport; use modals/drawers for secondary actions
2. **Dashboard pages**: Use grid layouts; each widget should have a max height with internal scroll
3. **Data-heavy pages**: Use virtualized lists or paginated tables; never render 100+ items at once
4. **Multi-section pages**: Use tabs, accordions, or a sidebar navigation to switch between sections

### Examples

```tsx
// ✅ CORRECT - Tabbed interface for multiple sections
<Tabs value={activeTab}>
  <Tab label="Overview" />
  <Tab label="Details" />
  <Tab label="Analytics" />
</Tabs>
<TabPanel value={activeTab} index={0}>
  <OverviewContent />
</TabPanel>

// ✅ CORRECT - Scrollable table with max height
<Box sx={{ maxHeight: 'var(--ob-max-height-table)', overflow: 'auto' }}>
  <DataTable rows={data} />
</Box>

// ✅ CORRECT - Viewport-height layout with flex
<Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
  <Header />
  <Box sx={{ flex: 1, overflow: 'auto' }}>
    <MainContent />
  </Box>
</Box>

// ❌ WRONG - Stacking many sections vertically
<Box>
  <Section1 />  {/* 400px tall */}
  <Section2 />  {/* 300px tall */}
  <Section3 />  {/* 500px tall */}
  <Section4 />  {/* 400px tall */}
  <Section5 />  {/* 600px tall */}
  {/* Total: 2200px - requires excessive scrolling */}
</Box>

// ❌ WRONG - Rendering all items without virtualization
<Box>
  {items.map(item => <LargeCard key={item.id} {...item} />)}  {/* 500+ items */}
</Box>
```

### Workspace Page Pattern

For complex workspace pages (like Finance, CAD, Feasibility):

1. **Fixed toolbar area**: Pinned actions, project selector
2. **Tab navigation**: Switch between views (not stacked vertically)
3. **Active tab content**: Only render current tab; use `minHeight` not fixed height
4. **Internal scrolling**: Each tab panel scrolls independently if needed

```tsx
// Recommended workspace layout
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

## Master-Detail Layout Pattern

For any page with primary content + selection/control panel, use a 2:1 grid layout. This pattern applies to dashboards, analytics, configuration screens, and any view with a main visualization plus a selector sidebar.

**Use Cases:** Finance scenarios, CAD configurations, project comparisons, analytics dashboards, report builders.

| Column         | Width            | Content                               |
| -------------- | ---------------- | ------------------------------------- |
| Left (Master)  | `xs={12} lg={8}` | Chart, visualization, primary content |
| Right (Detail) | `xs={12} lg={4}` | Scenario selector, controls, filters  |

### Layout Structure

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

### Why This Pattern

1. **Dense single-screen design** - Reduces scrolling by keeping chart and controls visible together
2. **Progressive disclosure** - Details reveal on selection without page navigation
3. **Responsive** - Stacks vertically on mobile (xs=12), side-by-side on desktop (lg=8/4)

---

## Selection Card List Pattern

Vertical list of clickable cards for switching between items, options, or configurations. Use this pattern for any sidebar selector where users choose from a list of options.

**Use Cases:** Scenario selectors, configuration profiles, project lists, template pickers, filter presets, saved searches.

### Visual States

| State                | Styling                                                                             |
| -------------------- | ----------------------------------------------------------------------------------- |
| **Default**          | `bgcolor: 'background.paper'`, `border: 1`, `borderColor: 'divider'`                |
| **Hover**            | `borderColor: 'primary.main'`, `boxShadow: 2`                                       |
| **Active**           | `bgcolor: alpha(primary, 0.05)`, `borderColor: alpha(primary, 0.3)`, `boxShadow: 1` |
| **Active Indicator** | `8px` dot (`borderRadius: '50%'`, `bgcolor: 'primary.main'`)                        |

### Component Structure

```tsx
<Box
    component="button"
    onClick={() => onSelect(item.id)}
    sx={{
        width: '100%',
        textAlign: 'left',
        p: 'var(--ob-space-100)',
        borderRadius: 'var(--ob-radius-sm)',
        border: 1,
        borderColor: isActive
            ? alpha(theme.palette.primary.main, 0.3)
            : 'divider',
        bgcolor: isActive
            ? alpha(theme.palette.primary.main, 0.05)
            : 'background.paper',
        boxShadow: isActive ? 1 : 0,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        '&:hover': { borderColor: 'primary.main', boxShadow: 2 },
    }}
>
    <Box
        sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
        }}
    >
        <Typography
            sx={{
                fontWeight: 700,
                color: isActive ? 'primary.dark' : 'text.primary',
            }}
        >
            {item.name}
        </Typography>
        {isActive && (
            <Box
                sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: 'primary.main',
                }}
            />
        )}
    </Box>
    <Typography
        sx={{
            fontSize: 'var(--ob-font-size-sm)',
            color: isActive ? 'primary.main' : 'text.secondary',
        }}
    >
        {item.description}
    </Typography>
</Box>
```

---

## Underlined Tab Navigation Pattern

For secondary/tertiary navigation within a page section. Use this instead of MUI Tabs when you need custom styling or simpler behavior.

**Use Cases:** Sub-navigation within panels, switching between related views, filtering content by category, stepping through options.

### Visual Design

| Element        | Styling                                                                    |
| -------------- | -------------------------------------------------------------------------- |
| Container      | `borderBottom: 1, borderColor: 'divider'`                                  |
| Tab (inactive) | `borderBottom: 2`, `borderColor: 'transparent'`, `color: 'text.secondary'` |
| Tab (active)   | `borderBottom: 2`, `borderColor: 'primary.main'`, `color: 'primary.main'`  |
| Tab (hover)    | `color: 'text.primary'`, `bgcolor: 'transparent'`                          |

### Component Structure

```tsx
<Box
    sx={{ borderBottom: 1, borderColor: 'divider', mb: 'var(--ob-space-150)' }}
>
    <Box sx={{ display: 'flex', gap: 'var(--ob-space-200)' }}>
        {items.map((item) => (
            <Button
                key={item.id}
                onClick={() => onSelect(item.id)}
                sx={{
                    py: 'var(--ob-space-100)',
                    px: 'var(--ob-space-025)',
                    borderRadius: 0,
                    borderBottom: 2,
                    borderColor: isActive ? 'primary.main' : 'transparent',
                    color: isActive ? 'primary.main' : 'text.secondary',
                    fontWeight: 500,
                    fontSize: 'var(--ob-font-size-sm)',
                    textTransform: 'none',
                    '&:hover': {
                        color: 'text.primary',
                        bgcolor: 'transparent',
                    },
                }}
            >
                {item.label}
            </Button>
        ))}
    </Box>
</Box>
```

---

## Enhanced Data Table Pattern

For professional data tables with type/status badges, styled headers, and summary rows. Use this pattern for any tabular data that needs a polished appearance.

**Use Cases:** Financial tables, inventory lists, user management, audit logs, configuration tables, any data grid requiring status indicators.

### Table Structure

| Element           | Styling                                                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------------------------------- |
| Card wrapper      | `GlassCard sx={{ overflow: 'hidden' }}`                                                                               |
| Header row        | `bgcolor: alpha(background.default, 0.5)`, includes title + context info                                              |
| Column headers    | `textTransform: 'uppercase'`, `letterSpacing: 'var(--ob-letter-spacing-wider)'`, `fontSize: 'var(--ob-font-size-xs)'` |
| Numeric columns   | `textAlign: 'right'`, `fontFamily: 'var(--ob-font-family-mono)'`                                                      |
| Status/Type badge | `StatusChip` with appropriate status color                                                                            |
| Summary/Total row | `bgcolor: alpha(background.default, 0.5)`, `fontWeight: 600`                                                          |
| Row hover         | `bgcolor: alpha(action.hover, 0.5)`                                                                                   |

### Component Structure

```tsx
<GlassCard sx={{ overflow: 'hidden' }}>
    {/* Header */}
    <Box
        sx={{
            px: 'var(--ob-space-150)',
            py: 'var(--ob-space-125)',
            borderBottom: 1,
            borderColor: 'divider',
            bgcolor: alpha(theme.palette.background.default, 0.5),
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
        }}
    >
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {t('table.title')}
        </Typography>
        <Typography
            sx={{ fontSize: 'var(--ob-font-size-sm)', color: 'text.secondary' }}
        >
            {contextInfo}
        </Typography>
    </Box>

    {/* Table with styled headers and status badges */}
    <Box
        component="table"
        sx={{
            width: '100%',
            '& th': {
                textTransform: 'uppercase',
                letterSpacing: 'var(--ob-letter-spacing-wider)',
                fontSize: 'var(--ob-font-size-xs)',
                fontWeight: 600,
            },
            '& th:nth-of-type(n+3), & td:nth-of-type(n+3)': {
                textAlign: 'right',
            },
        }}
    >
        {/* ... table content */}
    </Box>
</GlassCard>
```

### Status Badge Guidelines

| Category        | StatusChip Props           | Example Use                             |
| --------------- | -------------------------- | --------------------------------------- |
| Positive/Active | `status="success"` (green) | Approved, Active, Complete, Equity      |
| Informational   | `status="info"` (blue)     | Pending, In Progress, Primary, Debt     |
| Caution         | `status="warning"` (amber) | Review Needed, Expiring Soon, Mezzanine |
| Negative/Error  | `status="error"` (red)     | Failed, Rejected, Overdue               |
| Neutral         | `status="default"` (gray)  | Draft, Archived, N/A                    |

---

## Insight/Callout Box Pattern

For displaying AI-generated insights, analysis summaries, important notices, or contextual information with colored callout styling. Use this pattern to draw attention to key information.

**Use Cases:** AI recommendations, analysis summaries, important notices, validation feedback, contextual tips, warning messages, success confirmations.

### Visual Design

| Variant | Background                  | Border                     | Text Color     | When to Use                      |
| ------- | --------------------------- | -------------------------- | -------------- | -------------------------------- |
| Success | `alpha(success.main, 0.08)` | `alpha(success.main, 0.3)` | `success.dark` | Positive insights, confirmations |
| Info    | `alpha(primary.main, 0.08)` | `alpha(primary.main, 0.3)` | `primary.dark` | Neutral information, tips        |
| Warning | `alpha(warning.main, 0.08)` | `alpha(warning.main, 0.3)` | `warning.dark` | Caution, attention needed        |
| Error   | `alpha(error.main, 0.08)`   | `alpha(error.main, 0.3)`   | `error.dark`   | Critical issues, failures        |

### Component Structure

```tsx
<Box
    sx={{
        bgcolor: alpha(theme.palette.success.main, 0.08),
        border: 2,
        borderColor: alpha(theme.palette.success.main, 0.3),
        borderRadius: 'var(--ob-radius-sm)',
        p: 'var(--ob-space-150)',
    }}
>
    <Typography
        sx={{
            fontSize: 'var(--ob-font-size-sm)',
            fontWeight: 600,
            textTransform: 'uppercase',
            color: 'success.dark',
            letterSpacing: 'var(--ob-letter-spacing-wider)',
            mb: 'var(--ob-space-050)',
        }}
    >
        {t('common.analysis')} {/* "ANALYSIS", "TIP", "NOTE", etc. */}
    </Typography>
    <Typography
        sx={{
            fontSize: 'var(--ob-font-size-sm)',
            color: 'success.dark',
            lineHeight: 1.6,
        }}
    >
        {insightText}
    </Typography>
</Box>
```

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

## Chart & Data Visualization Standards (MANDATORY)

This project uses **Recharts** for all data visualizations. Charts must follow the same design token principles as other UI elements.

### Chart Library

| Requirement | Standard                                | Rationale                                   |
| ----------- | --------------------------------------- | ------------------------------------------- |
| Library     | **Recharts** only                       | Already installed, React-native, responsive |
| Container   | Wrap in `ResponsiveContainer`           | Ensures responsive behavior                 |
| Height      | Use `--ob-max-height-panel` (400px) max | Prevents viewport overflow                  |
| Colors      | Use theme palette via `useTheme()`      | Dark mode compatible                        |
| Labels      | Use i18n `t()` function                 | Internationalization                        |

### Chart Styling Requirements

| Element         | Standard                               | Token/Value               |
| --------------- | -------------------------------------- | ------------------------- |
| Bar corners     | Use radius `4`                         | Matches `--ob-radius-sm`  |
| Tooltip corners | Use radius `4`                         | Matches `--ob-radius-sm`  |
| Grid lines      | `vertical={false}`, stroke from theme  | Clean, minimal appearance |
| Axis lines      | `axisLine={false}`, `tickLine={false}` | Modern, minimal style     |
| Axis text       | `fontSize: 12`, `fill` from theme      | Use `text.secondary`      |
| Legend          | `wrapperStyle={{ paddingTop: 20 }}`    | Consistent spacing        |

### Chart Type Guidelines

| Use Case           | Chart Type     | Recharts Component            |
| ------------------ | -------------- | ----------------------------- |
| Compare categories | Stacked Bar    | `BarChart` with `stackId`     |
| Timeline with mix  | Composed       | `ComposedChart` (Bar + Line)  |
| Part of whole      | Donut/Pie      | `PieChart` with `innerRadius` |
| Trend over time    | Line           | `LineChart` or `AreaChart`    |
| Distribution       | Horizontal Bar | `BarChart layout="vertical"`  |

### Examples

```tsx
// ✅ CORRECT - Recharts bar chart with design tokens
import { useTheme, alpha } from '@mui/material'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from 'recharts'

function MyChart({ data }) {
    const theme = useTheme()

    return (
        <Box sx={{ height: 'var(--ob-max-height-panel)', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} barSize={60}>
                    <CartesianGrid
                        stroke={alpha(theme.palette.divider, 0.3)}
                        vertical={false}
                    />
                    <XAxis
                        dataKey="name"
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fill: theme.palette.text.secondary,
                            fontSize: 12,
                        }}
                    />
                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fill: theme.palette.text.secondary,
                            fontSize: 12,
                        }}
                    />
                    <Tooltip
                        contentStyle={{
                            borderRadius: 4, // --ob-radius-sm
                            border: 'none',
                            boxShadow: theme.shadows[2],
                        }}
                    />
                    <Bar
                        dataKey="equity"
                        stackId="a"
                        fill={theme.palette.success.main}
                        radius={[0, 0, 4, 4]} // Bottom corners rounded
                    />
                    <Bar
                        dataKey="debt"
                        stackId="a"
                        fill={theme.palette.primary.main}
                        radius={[4, 4, 0, 0]} // Top corners rounded
                    />
                </BarChart>
            </ResponsiveContainer>
        </Box>
    )
}

// ❌ WRONG - Hardcoded colors and missing responsive container
;<BarChart data={data} height={400}>
    <Bar dataKey="value" fill="#3b82f6" /> // Hardcoded hex color!
</BarChart>

// ❌ WRONG - Using non-Recharts library
import { Chart } from 'chart.js' // Wrong library!
```

### Composed Chart Pattern (Bar + Line)

For showing both cumulative and periodic data (like drawdown schedules):

```tsx
// ✅ CORRECT - ComposedChart with bars and line overlay
<ComposedChart data={data}>
    <CartesianGrid
        stroke={alpha(theme.palette.divider, 0.3)}
        vertical={false}
    />
    <XAxis dataKey="period" axisLine={false} tickLine={false} />
    <YAxis yAxisId="left" axisLine={false} tickLine={false} />
    <YAxis
        yAxisId="right"
        orientation="right"
        axisLine={false}
        tickLine={false}
    />

    {/* Stacked bars for periodic values */}
    <Bar
        yAxisId="left"
        dataKey="equityDraw"
        stackId="a"
        fill={theme.palette.success.main}
    />
    <Bar
        yAxisId="left"
        dataKey="debtDraw"
        stackId="a"
        fill={theme.palette.primary.main}
    />

    {/* Line for cumulative/running total */}
    <Line
        yAxisId="right"
        type="monotone"
        dataKey="outstandingDebt"
        stroke={theme.palette.text.primary}
        strokeWidth={2}
        dot={{ r: 3, fill: theme.palette.text.primary }}
    />
</ComposedChart>
```

---

## Metrics Grid Pattern (MANDATORY)

For displaying KPIs, financial metrics, or summary statistics, use a responsive 4-column grid:

```tsx
// ✅ CORRECT - Metrics grid with GlassCard
<Grid container spacing="var(--ob-space-100)">
  <Grid item xs={6} md={3}>
    <GlassCard sx={{ p: 'var(--ob-space-100)' }}>
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-sm)',
          color: 'text.secondary',
          mb: 'var(--ob-space-025)'
        }}
      >
        {t('finance.metrics.totalCost')}
      </Typography>
      <Typography
        sx={{
          fontSize: 'var(--ob-font-size-2xl)',
          fontWeight: 700,
          color: 'text.primary'
        }}
      >
        {formatCurrency(value)}
      </Typography>
    </GlassCard>
  </Grid>
  {/* Repeat for other metrics */}
</Grid>

// ❌ WRONG - Hardcoded Tailwind classes
<div className="grid grid-cols-4 gap-4">
  <div className="bg-white p-4 rounded-xl">
    <div className="text-sm text-gray-500">Total Cost</div>
    <div className="text-2xl font-bold">$1,000,000</div>
  </div>
</div>
```

### Metric Card Guidelines

| Element   | Standard                                                        |
| --------- | --------------------------------------------------------------- |
| Container | `GlassCard` with `p: 'var(--ob-space-100)'`                     |
| Label     | `fontSize: 'var(--ob-font-size-sm)'`, `color: 'text.secondary'` |
| Value     | `fontSize: 'var(--ob-font-size-2xl)'`, `fontWeight: 700`        |
| Grid      | `xs={6} md={3}` for 2-column mobile, 4-column desktop           |
| Spacing   | `spacing="var(--ob-space-100)"` between cards                   |

---

## Pre-Commit Validation

The project includes ESLint rules to catch violations. Run before committing:

```bash
cd frontend && npm run lint
```

---

## Quick Reference Card

```
SPACING:    var(--ob-space-XXX)     where XXX = 025|050|075|100|125|150|175|200|250|300|400|500|600|800
RADIUS:     var(--ob-radius-XXX)    where XXX = none|xs|sm|md|lg|pill
FONT SIZE:  var(--ob-font-size-XXX) where XXX = 2xs|xs|sm-minus|sm|md|base|lg|xl|2xl|3xl|4xl|5xl
ICON SIZE:  var(--ob-size-icon-XXX) where XXX = sm|md|lg|xl
BLUR:       var(--ob-blur-XXX)      where XXX = sm|xs|md|xl|lg
Z-INDEX:    var(--ob-z-XXX)         where XXX = base|dropdown|sticky|fixed|modal-backdrop|modal|popover|tooltip
HEIGHT:     var(--ob-max-height-XXX) where XXX = panel (400px)|table (500px)|card-group (600px)

CHARTS:     Library: Recharts only | Container: ResponsiveContainer | Height: --ob-max-height-panel
            Bar radius: 4 | Colors: theme.palette.* | Axis: axisLine={false} tickLine={false}
```

---

## AI Agent Checklist

Before submitting UI code changes, verify:

**Token Usage:**

- [ ] No hardcoded pixel values (use `--ob-space-*` or `--ob-size-*`)
- [ ] No hardcoded spacing (`px`/`rem`); prefer `--ob-space-*` or tokenized MUI spacing numbers
- [ ] No hardcoded border-radius (use `--ob-radius-*`)
- [ ] Cards/panels use `--ob-radius-sm` (4px), NOT `--ob-radius-lg`
- [ ] Buttons use `--ob-radius-xs` (2px)
- [ ] Modals/dialogs use `--ob-radius-lg` (8px)
- [ ] No hardcoded colors (use theme or tokens)
- [ ] Using canonical components where available
- [ ] Font sizes use `--ob-font-size-*` tokens

**Layout & Viewport:**

- [ ] Page fits within ~2 viewport heights maximum (no excessive scrolling)
- [ ] Multi-section content uses tabs, accordions, or collapsible panels (NOT vertical stacking)
- [ ] Data tables have `maxHeight` with internal scroll
- [ ] Workspace pages follow the fixed-toolbar + tabs + scrollable-content pattern
- [ ] Large lists use virtualization or pagination (never render 100+ items at once)
- [ ] Tab content only renders when active (lazy loading)

**Charts & Visualizations:**

- [ ] Using Recharts (not other chart libraries)
- [ ] Chart wrapped in `ResponsiveContainer`
- [ ] Chart height ≤ `--ob-max-height-panel` (400px)
- [ ] Bar corners use radius `4` (matches `--ob-radius-sm`)
- [ ] Colors from theme palette (not hardcoded hex)
- [ ] Axis lines disabled (`axisLine={false}`, `tickLine={false}`)
- [ ] Chart labels use i18n `t()` function
- [ ] Custom tooltips styled with design tokens

**Metrics Grid:**

- [ ] Using `GlassCard` for metric containers
- [ ] Grid uses `xs={6} md={3}` for responsive 2/4 columns
- [ ] Label uses `--ob-font-size-sm`, `text.secondary`
- [ ] Value uses `--ob-font-size-2xl`, `fontWeight: 700`

**Layout Patterns:**

- [ ] Master-Detail layouts use Grid `xs={12} lg={8}` / `xs={12} lg={4}` split
- [ ] Selection card lists have proper active state styling (alpha bg, dot indicator)
- [ ] Underlined tabs use border-bottom styling (not MUI Tabs component for simple cases)
- [ ] Data tables use GlassCard wrapper with header row
- [ ] Status badges use StatusChip with appropriate status colors
- [ ] Total/summary rows have gray background (`alpha(background.default, 0.5)`)
- [ ] Insight/callout boxes use alpha-transparency backgrounds with matching borders
