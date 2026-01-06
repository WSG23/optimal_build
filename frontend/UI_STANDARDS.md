# UI Design Standards for AI Agents

> **CRITICAL**: AI agents MUST follow these standards when writing or modifying UI code.
> This document is the source of truth for design token VALUES.

---

## Document Map

| Document                                          | Purpose                                               | When to Read                  |
| ------------------------------------------------- | ----------------------------------------------------- | ----------------------------- |
| **UI_STANDARDS.md** (this file)                   | Token values (spacing, radius, colors, typography)    | When writing CSS/styling      |
| **[UX_ARCHITECTURE.md](./UX_ARCHITECTURE.md)**    | Layout patterns, decision trees, AI Studio principles | When designing page structure |
| **[STYLE_GUIDE.md](./src/styles/STYLE_GUIDE.md)** | CSS class architecture, BEM naming                    | When adding new CSS classes   |

---

## Quick Start: Common Lookups

**Most common decisions - jump directly to what you need:**

### 1. Which component should I use?

| I need...            | Use                          | Jump to                                                           |
| -------------------- | ---------------------------- | ----------------------------------------------------------------- |
| Container on page bg | `GlassCard`                  | [Component Selection Matrix](#component-selection-matrix)         |
| Nested container     | `Card` (opaque, no blur)     | [Quick Decision Tree](#quick-decision-card-vs-glasscard-vs-panel) |
| Metric display       | `HeroMetric` or `MetricCard` | [Component Selection Matrix](#component-selection-matrix)         |
| Status indicator     | `StatusChip`                 | [Component Selection Matrix](#component-selection-matrix)         |
| Button               | `Button`                     | [Component Selection Matrix](#component-selection-matrix)         |

### 2. What token should I use?

| For...               | Token                  | Value    |
| -------------------- | ---------------------- | -------- |
| Card border radius   | `--ob-radius-sm`       | 4px      |
| Button border radius | `--ob-radius-xs`       | 2px      |
| Modal border radius  | `--ob-radius-lg`       | 8px      |
| Default padding      | `--ob-space-100`       | 16px     |
| Section gap          | `--ob-space-150`       | 24px     |
| Glass blur           | `--ob-blur-md`         | 12px     |
| Glass background     | `--ob-surface-glass-1` | 3% white |

### 3. Quick validation checklist

Before submitting UI code, verify:

- [ ] No hardcoded `px` values (use `--ob-space-*`, `--ob-radius-*`)
- [ ] No MUI `spacing={N}` (use `spacing="var(--ob-space-*)"`)
- [ ] Cards use `--ob-radius-sm` (4px), NOT larger
- [ ] Buttons use `--ob-radius-xs` (2px)
- [ ] Using canonical components from `src/components/canonical/`
- [ ] No nested glass surfaces with blur (causes scroll lock)

---

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

### Spacing Hierarchy (MANDATORY)

Use different spacing values to communicate information hierarchy **without wrappers**. Larger gaps = higher-level separation.

| Context                     | Token            | Value | Purpose                                      |
| --------------------------- | ---------------- | ----- | -------------------------------------------- |
| Between top-level sections  | `--ob-space-300` | 48px  | Property Overview → Condition Assessment     |
| Between sibling containers  | `--ob-space-150` | 24px  | PATH grid → INTEL_FEED → Footer (same level) |
| Between cards within a grid | `--ob-space-150` | 24px  | Card to card in same grid                    |
| Within card content         | `--ob-space-100` | 16px  | Internal padding, tight groupings            |

**Key Rule: Use section's `gap` property, NOT child `margin`**

When sibling containers (PATH grid, INTEL_FEED, Footer) are at the same hierarchy level within a section, they should have **equal gaps**. Never add `margin-bottom` to individual children - this creates unequal spacing.

```css
/* ✅ CORRECT - Single gap property on parent */
.my-section {
    display: flex;
    flex-direction: column;
    gap: var(--ob-space-150); /* All children spaced equally */
}

/* ❌ WRONG - Margin on child creates double spacing */
.my-section__first-child {
    margin-bottom: var(--ob-space-200); /* 32px + 24px gap = 56px total! */
}
```

**Visual Hierarchy Example:**

```
┌─────────────────────────────────────────────────────────────────┐
│ SECTION A (e.g., Multi-Scenario Comparison)                     │
│                                                                 │
│   ┌─ PATH Grid ─────────────────────────────────────────────┐   │
│   │  [Card] [Card] [Card]  ← 24px gap between cards         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ↕ 24px (section gap - same for all siblings)                  │
│                                                                 │
│   ┌─ INTEL_FEED ────────────────────────────────────────────┐   │
│   │  [Intel Tape] [Intel Tape]  ← 24px gap                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ↕ 24px (section gap - equal to above)                         │
│                                                                 │
│   ┌─ Subsection: EXPORT_PROTOCOL ──────────────────────────┐   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

↕ 48px (section gap)

┌─────────────────────────────────────────────────────────────────┐
│ SECTION B (e.g., Property Condition Assessment)                 │
└─────────────────────────────────────────────────────────────────┘
```

**CSS Implementation:**

```css
/* Top-level sections use 48px gap */
.page-content {
    display: flex;
    flex-direction: column;
    gap: var(--ob-space-300); /* 48px between sections */
}

/* Section container uses 24px gap for ALL sibling children */
.my-section {
    display: flex;
    flex-direction: column;
    gap: var(--ob-space-150); /* 24px - uniform for all siblings */
}

/* Grid uses same 24px gap for cards within */
.my-section__grid {
    display: grid;
    gap: var(--ob-space-150); /* 24px between cards */
    /* NO margin-bottom here! Let parent's gap handle spacing */
}
```

**TSX Example:**

```tsx
// ✅ CORRECT - Hierarchy via spacing tokens
<Stack spacing="var(--ob-space-300)">
    {' '}
    {/* 48px between sections */}
    <section className="multi-scenario">
        {' '}
        {/* 24px gap via CSS */}
        <div className="multi-scenario__path-grid">
            <PathCard />
            <PathCard />
        </div>
        {/* 24px gap (from section) - equal to all siblings */}
        <div className="multi-scenario__intel-feed">...</div>
        {/* 24px gap - same as above (no special treatment) */}
        <div className="multi-scenario__export-console">...</div>
    </section>
    <section className="condition-assessment">...</section>
</Stack>
```

---

## Size Standards (MANDATORY)

| Token                        | Value  | Use Cases                  |
| ---------------------------- | ------ | -------------------------- |
| `--ob-size-icon-sm`          | 24px   | Small icons                |
| `--ob-size-icon-md`          | 32px   | Default icons              |
| `--ob-size-icon-lg`          | 48px   | Large icons, avatars       |
| `--ob-size-icon-xl`          | 64px   | Hero icons                 |
| `--ob-size-drop-zone`        | 120px  | File drop zones min-height |
| `--ob-size-controls-min`     | 400px  | Control bars min-width     |
| `--ob-max-width-content`     | 1000px | Content max-width          |
| `--ob-max-width-page`        | 1400px | Page max-width             |
| `--ob-max-height-panel`      | 400px  | Scrollable panels          |
| `--ob-max-height-table`      | 500px  | Data tables with scroll    |
| `--ob-max-height-card-group` | 600px  | Grouped cards with scroll  |

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

| Token           | Value | Use Cases                    |
| --------------- | ----- | ---------------------------- |
| `--ob-blur-sm`  | 4px   | Subtle blur                  |
| `--ob-blur-xs`  | 8px   | Light glass surfaces         |
| `--ob-blur-md`  | 12px  | Standard glass effect        |
| `--ob-blur-xl`  | 16px  | Strong glass surfaces        |
| `--ob-blur-lg`  | 24px  | Heavy blur                   |
| `--ob-blur-2xl` | 40px  | Deep glass, premium overlays |

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

## Functional Color Language

This project uses a **"Mission Control" aesthetic** with Cyan as primary brand and semantic colors for functional meaning.

### Color Roles

| Color          | Token                                   | Purpose                                              |
| -------------- | --------------------------------------- | ---------------------------------------------------- |
| **Cyan**       | `var(--ob-color-neon-cyan)`             | Brand/selection (active tabs, primary CTA, logo)     |
| **Green**      | `success.main`, `var(--ob-success-500)` | Vitality/success (live, active, positive trends)     |
| **Red**        | `error.main`, `var(--ob-error-500)`     | Errors/critical (failed, delete, negative)           |
| **Amber**      | `warning.main`, `var(--ob-warning-500)` | Caution/attention (offline, critical path, warnings) |
| **Indigo**     | `info.main`, `var(--ob-info-500)`       | Categories/AI (data differentiation, intelligence)   |
| **Slate/Gray** | `text.primary`, `text.secondary`        | Neutral hierarchy                                    |

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
| Category differentiation  | Indigo        | `status="info"`             |
| AI Intelligence indicator | Indigo        | `status="info"`             |
| Neutral/Draft status      | Gray          | `status="neutral"`          |

> **For detailed decision trees and usage patterns, see [UX_ARCHITECTURE.md](./UX_ARCHITECTURE.md)**

---

## Dark Mode vs Light Mode Standards

This project defaults to **dark mode** (fullscreen professional app convention). Both modes are fully supported via CSS custom properties that automatically switch based on `data-theme` attribute.

### Key Principles

| Aspect             | Dark Mode Strategy                            | Light Mode Strategy                      |
| ------------------ | --------------------------------------------- | ---------------------------------------- |
| **Elevation**      | Lighter surface = more elevated               | Shadow depth = more elevated             |
| **Text**           | Off-white (`#f1f5f9`), NOT pure white         | Near-black (`#0f172a`)                   |
| **Hover states**   | White overlay to "lift" (`rgba(255,255,255)`) | Black overlay to "dim" (`rgba(0,0,0)`)   |
| **Borders**        | Low opacity white (8%)                        | Higher opacity black (12%)               |
| **Glass effects**  | Very transparent (3-5%)                       | More opaque (40-55%) "frosted ice"       |
| **Shadows**        | Minimal, near-black                           | More prominent, gray tones               |
| **Status colors**  | Lighter shades (400) for text                 | Darker shades (600-700) for text         |
| **Selected items** | Cyan tint (`--ob-color-action-selected`)      | Blue tint (`--ob-color-action-selected`) |

### Interactive State Tokens

Use these tokens for consistent hover/active/selected feedback across both modes:

| Token                               | Dark Mode Value          | Light Mode Value        | Use Case                   |
| ----------------------------------- | ------------------------ | ----------------------- | -------------------------- |
| `--ob-color-action-hover`           | `rgba(255,255,255,0.08)` | `rgba(0,0,0,0.05)`      | Hoverable elements         |
| `--ob-color-action-active`          | `rgba(255,255,255,0.12)` | `rgba(0,0,0,0.1)`       | Pressed/active state       |
| `--ob-color-action-selected`        | `rgba(0,243,255,0.1)`    | `rgba(59,130,246,0.1)`  | Selected items (cyan/blue) |
| `--ob-color-action-selected-strong` | `rgba(0,243,255,0.15)`   | `rgba(59,130,246,0.15)` | Emphasized selection       |
| `--ob-color-action-focus-ring`      | `rgba(59,130,246,0.5)`   | `rgba(59,130,246,0.4)`  | Focus indicators           |

### Input Surface Tokens

Form inputs need distinct surfaces from their container cards:

| Token                               | Dark Mode Value          | Light Mode Value | Use Case               |
| ----------------------------------- | ------------------------ | ---------------- | ---------------------- |
| `--ob-color-surface-input`          | `rgba(255,255,255,0.04)` | `#ffffff`        | Input field background |
| `--ob-color-surface-input-hover`    | `rgba(255,255,255,0.06)` | `#f8fafc`        | Input hover state      |
| `--ob-color-surface-input-focus`    | `rgba(255,255,255,0.08)` | `#ffffff`        | Input focus state      |
| `--ob-color-surface-input-disabled` | `rgba(255,255,255,0.02)` | `#f1f5f9`        | Disabled input         |

### Table/List Surface Tokens

For data-dense views with row alternation:

| Token                           | Dark Mode Value          | Light Mode Value        | Use Case                   |
| ------------------------------- | ------------------------ | ----------------------- | -------------------------- |
| `--ob-color-table-row-alt`      | `rgba(255,255,255,0.02)` | `rgba(0,0,0,0.02)`      | Alternating row background |
| `--ob-color-table-row-hover`    | `rgba(0,243,255,0.05)`   | `rgba(59,130,246,0.05)` | Row hover (brand tint)     |
| `--ob-color-table-row-selected` | `rgba(0,243,255,0.08)`   | `rgba(59,130,246,0.1)`  | Selected row               |
| `--ob-color-table-header`       | `rgba(255,255,255,0.03)` | `rgba(0,0,0,0.03)`      | Table header background    |

### CSS Usage Examples

```css
/* ✅ CORRECT - Interactive list item */
.list-item {
    background: transparent;
    transition: background 0.15s ease;
}
.list-item:hover {
    background: var(--ob-color-action-hover);
}
.list-item:active {
    background: var(--ob-color-action-active);
}
.list-item--selected {
    background: var(--ob-color-action-selected);
}

/* ✅ CORRECT - Form input */
.form-input {
    background: var(--ob-color-surface-input);
    border: 1px solid var(--ob-color-border-subtle);
}
.form-input:hover {
    background: var(--ob-color-surface-input-hover);
}
.form-input:focus {
    background: var(--ob-color-surface-input-focus);
    border-color: var(--ob-color-border-focus);
}

/* ✅ CORRECT - Data table */
.table-row:nth-child(even) {
    background: var(--ob-color-table-row-alt);
}
.table-row:hover {
    background: var(--ob-color-table-row-hover);
}
.table-row--selected {
    background: var(--ob-color-table-row-selected);
}
```

### Dark Mode Anti-Patterns

```css
/* ❌ WRONG - Pure white text causes eye strain */
color: #ffffff;

/* ✅ CORRECT - Off-white */
color: var(--ob-color-text-primary); /* #f1f5f9 */

/* ❌ WRONG - Hardcoded dark mode value won't switch in light mode */
background: rgba(255, 255, 255, 0.05);

/* ✅ CORRECT - Token automatically switches */
background: var(--ob-color-action-hover);

/* ❌ WRONG - Same status color intensity for both modes */
color: #ef4444; /* Too harsh on dark bg */

/* ✅ CORRECT - Use -text variant for dark mode */
color: var(--ob-error-text); /* #f87171 - lighter for dark bg */
```

### Testing Both Modes

Before submitting UI changes:

1. Toggle theme via UI (click moon/sun icon in navbar)
2. Verify all interactive states are visible in both modes
3. Check text contrast meets WCAG AA (4.5:1 for normal text)
4. Ensure status colors are distinguishable in both modes

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

### Component Selection Matrix

Use this matrix to quickly identify which canonical component to use for your UI need:

| I need to...                          | Use this component       | Import from                               |
| ------------------------------------- | ------------------------ | ----------------------------------------- |
| Wrap content in a glass surface       | `GlassCard`              | `components/canonical/GlassCard`          |
| Display a single key metric           | `HeroMetric`             | `components/canonical/HeroMetric`         |
| Display metric with trend/sparkline   | `PremiumMetricCard`      | `components/canonical/PremiumMetricCard`  |
| Display a compact metric tile         | `MetricTile`             | `components/canonical/MetricTile`         |
| Display a metric with description     | `MetricCard`             | `components/canonical/MetricCard`         |
| Show status indicator (success/error) | `StatusChip`             | `components/canonical/StatusChip`         |
| Show a small label tag                | `Tag`                    | `components/canonical/Tag`                |
| Create a primary/secondary button     | `Button`                 | `components/canonical/Button`             |
| Create a glass-effect button          | `GlassButton`            | `components/canonical/GlassButton`        |
| Create a text input field             | `Input`                  | `components/canonical/Input`              |
| Create a page section header          | `SectionHeader`          | `components/canonical/SectionHeader`      |
| Create an animated page header        | `AnimatedPageHeader`     | `components/canonical/AnimatedPageHeader` |
| Display glowing/neon text             | `NeonText`               | `components/canonical/NeonText`           |
| Show a pulsing status dot             | `PulsingStatusDot`       | `components/canonical/PulsingStatusDot`   |
| Create tab navigation                 | `Tabs`                   | `components/canonical/Tabs`               |
| Display an alert/notification         | `AlertBlock`             | `components/canonical/AlertBlock`         |
| Show empty state message              | `EmptyState`             | `components/canonical/EmptyState`         |
| Display a data block with label       | `DataBlock`              | `components/canonical/DataBlock`          |
| Show loading skeleton                 | `Skeleton`               | `components/canonical/Skeleton`           |
| Create a panel container              | `Panel`                  | `components/canonical/Panel`              |
| Create a window-like container        | `Window` / `GlassWindow` | `components/canonical/Window`             |
| Create a basic card container         | `Card`                   | `components/canonical/Card`               |

### Component → Token Mapping

Each canonical component uses specific design tokens. Reference this when customizing:

| Component            | Background Token       | Border Radius Token | Blur Token     | Other Tokens               |
| -------------------- | ---------------------- | ------------------- | -------------- | -------------------------- |
| `GlassCard`          | `--ob-surface-glass-1` | `--ob-radius-sm`    | `--ob-blur-md` | `--ob-color-border-subtle` |
| `Card`               | `--ob-color-bg-muted`  | `--ob-radius-sm`    | —              | `--ob-color-border-subtle` |
| `Panel`              | `--ob-surface-glass-1` | `--ob-radius-sm`    | `--ob-blur-md` | —                          |
| `Button` (primary)   | cyan gradient          | `--ob-radius-xs`    | —              | `--ob-glow-neon-cyan`      |
| `Button` (secondary) | transparent            | `--ob-radius-xs`    | —              | `--ob-color-border-subtle` |
| `GlassButton`        | `--ob-surface-glass-1` | `--ob-radius-xs`    | `--ob-blur-sm` | —                          |
| `Input`              | `--ob-color-bg-muted`  | `--ob-radius-md`    | —              | `--ob-color-border-subtle` |
| `StatusChip`         | semantic color based   | `--ob-radius-xs`    | —              | status prop → color        |
| `Tag`                | `--ob-color-bg-muted`  | `--ob-radius-xs`    | —              | —                          |
| `HeroMetric`         | transparent            | —                   | —              | `--ob-font-size-3xl`       |
| `PremiumMetricCard`  | `--ob-surface-glass-1` | `--ob-radius-sm`    | `--ob-blur-md` | `--ob-glow-neon-cyan`      |
| `MetricCard`         | `--ob-surface-glass-1` | `--ob-radius-sm`    | —              | —                          |
| `MetricTile`         | `--ob-color-bg-muted`  | `--ob-radius-sm`    | —              | —                          |
| `AlertBlock`         | semantic color based   | `--ob-radius-sm`    | —              | severity prop → color      |
| `EmptyState`         | transparent            | —                   | —              | `--ob-color-text-tertiary` |
| `Tabs`               | transparent            | `--ob-radius-xs`    | —              | `--ob-color-neon-cyan`     |
| `NeonText`           | —                      | —                   | —              | `--ob-glow-neon-cyan`      |
| `PulsingStatusDot`   | semantic color based   | `--ob-radius-pill`  | —              | `--ob-glow-status-*`       |
| `Skeleton`           | `--ob-color-bg-muted`  | `--ob-radius-sm`    | —              | animation built-in         |

### Quick Decision: Card vs GlassCard vs Panel

```
Need a container?
│
├─ On page background (Level 0 floor)?
│   └─ Use GlassCard (glass-1 with blur)
│
├─ Inside another card (nested)?
│   └─ Use Card (opaque, no blur - prevents scroll lock)
│
├─ Floating/modal overlay?
│   └─ Use Panel or GlassWindow
│
└─ Simple content grouping?
    └─ Use Card (minimal styling)
```

---

## Disabled Button States (MANDATORY)

When a button is disabled due to missing prerequisites, users need clear feedback about what's required.

**Problem:** Disabled buttons without explanation cause confusion ("Why can't I click this?")

**Solution:** Communicate prerequisites through button text, tooltips, and visible status indicators.

### Implementation Pattern

```tsx
// ✅ CORRECT - Disabled state with explanation
<Button
  variant="primary"
  disabled={!canSubmit}
  title={prerequisites.length === 0 ? 'Select at least one scenario first' : undefined}
>
  {prerequisites.length === 0 ? 'SELECT SCENARIO' : 'CAPTURE'}
</Button>

// Also show prerequisite status nearby
<div className="scenario-badge">
  <span className="count">{selectedScenarios.length}</span>
  <span className="label">SCENARIOS</span>
</div>

// ❌ WRONG - Just gray out with no explanation
<Button disabled={!canSubmit}>
  Capture
</Button>
```

### Key Rules

| Rule             | Requirement                                                                   |
| ---------------- | ----------------------------------------------------------------------------- |
| Button Text      | Change to show required action (e.g., "SELECT SCENARIO" instead of "CAPTURE") |
| Tooltip          | Add `title` attribute explaining what's needed                                |
| Status Indicator | Show count/badge of prerequisites nearby                                      |
| Visual Feedback  | Disabled styling (grayed out) + text change                                   |

### Common Patterns

| State                 | Button Text       | Tooltip                                   |
| --------------------- | ----------------- | ----------------------------------------- |
| No scenarios selected | "SELECT SCENARIO" | "Select at least one scenario to capture" |
| No files selected     | "SELECT FILES"    | "Choose files to upload first"            |
| Form incomplete       | "COMPLETE FORM"   | "Fill required fields to continue"        |
| Loading               | "LOADING..."      | N/A (show spinner)                        |

---

## Theme-Agnostic Button/Control Styling (MANDATORY)

For controls that must work in both light and dark modes, especially map controls and floating UI elements.

**Problem:** Buttons styled with dark theme tokens become invisible in light mode:

- `--ob-neutral-900` appears as near-black background
- Dark icons on dark background = invisible
- Users can't identify or interact with controls

**Solution:** Use explicit light-on-dark or dark-on-light styling that works in both modes.

### Map Control Pattern (Recommended)

```tsx
// ✅ CORRECT - Theme-agnostic map control
<IconButton
  sx={{
    bgcolor: 'white',                              // Explicit white background
    border: '1px solid rgba(0, 0, 0, 0.2)',       // Visible border
    borderRadius: 'var(--ob-radius-xs)',          // Machined edge
    boxShadow: '0 2px 6px rgba(0,0,0,0.2)',       // Depth
    color: '#333',                                 // Dark icon color
    '&:hover': {
      bgcolor: 'var(--ob-color-neon-cyan-muted)', // Brand color on hover
      color: 'var(--ob-color-neon-cyan)',
      borderColor: 'var(--ob-color-neon-cyan)',
    },
  }}
>
  <MyLocationIcon />
</IconButton>

// ❌ WRONG - Dark theme only
<IconButton
  sx={{
    bgcolor: 'var(--ob-neutral-900)',   // Black - invisible in light mode
    color: 'var(--ob-color-text-primary)',
  }}
>
  <MyLocationIcon />
</IconButton>
```

### Key Rules

| Rule       | Light Mode                    | Dark Mode                 |
| ---------- | ----------------------------- | ------------------------- |
| Background | `white` or `background.paper` | Works (appears as white)  |
| Border     | `rgba(0, 0, 0, 0.2)`          | Works (subtle on dark)    |
| Icon Color | `#333` or `text.primary`      | Works (inverts via theme) |
| Shadow     | `rgba(0,0,0,0.2)`             | Works (provides depth)    |

### When to Use Theme-Agnostic Styling

| Context                       | Use Theme-Agnostic | Use Theme Tokens        |
| ----------------------------- | ------------------ | ----------------------- |
| Map controls (zoom, recenter) | ✅ Always          | ❌                      |
| Floating action buttons       | ✅ Always          | ❌                      |
| Overlay controls              | ✅ Always          | ❌                      |
| Standard page buttons         | ❌                 | ✅ Use canonical Button |
| Cards and panels              | ❌                 | ✅ Use GlassCard        |

### Standard Map Control CSS

```css
.map-control {
    background: white;
    border: 1px solid rgba(0, 0, 0, 0.2);
    border-radius: var(--ob-radius-xs);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    color: #333;
    cursor: pointer;
    transition: all 0.15s ease;
}

.map-control:hover {
    background: var(--ob-color-neon-cyan-muted);
    color: var(--ob-color-neon-cyan);
    border-color: var(--ob-color-neon-cyan);
}
```

---

## Section Wrapper Anti-Pattern (AVOID)

**Problem:** Adding outer glass/seamless wrappers around sections that already contain cards creates:

- Wasted screen space (32px+ extra padding)
- Visual nesting fatigue ("cards inside cards")
- Inconsistent depth perception

### Visual Comparison

```
❌ WRONG: Nested wrappers (56px from edge to content)
┌─ Section ─────────────────────────────────────────┐
│ ┌─ Outer Glass Panel (32px padding) ────────────┐ │
│ │ ┌─ Card (24px padding) ─────────────────────┐ │ │
│ │ │ Content                                   │ │ │
│ │ └───────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────┘

✅ CORRECT: Flat structure (24px from edge to content)
┌─ Section (gap: 24px) ─────────────────────────────┐
│ Title (on background)                              │
│ ┌─ Card (24px padding) ─────────────────────────┐ │
│ │ Content                                        │ │
│ └────────────────────────────────────────────────┘ │
│ ┌─ Sibling Card ────────────────────────────────┐ │
│ │ Content                                        │ │
│ └────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────┘
```

### CSS Classes to Avoid at Section Level

- `ob-seamless-panel ob-seamless-panel--glass` as outer wrapper
- `__surface` classes containing multiple cards

### Correct Approach

```css
/* Section uses gap, not wrapper padding */
.my-section {
    display: flex;
    flex-direction: column;
    gap: var(--ob-space-150); /* 24px between children */
}

/* Cards are direct children */
.my-section__card {
    padding: var(--ob-space-150); /* 24px internal */
    background: var(--ob-surface-glass-1);
    border: 1px solid var(--ob-color-border-subtle);
    border-radius: var(--ob-radius-sm);
}
```

### Signals of Violation

- `__surface` wrapper class with `padding: var(--ob-space-200)` around cards
- Nested `.ob-seamless-panel` elements
- Total edge-to-content padding > 32px
- Visible "card inside card" borders

> **For detailed implementation examples and refactored components, see the Flat Section Pattern in [UX_ARCHITECTURE.md](./UX_ARCHITECTURE.md#flat-section-pattern-avoid-nested-wrappers)**

---

## Sibling Card Surface Standard (MANDATORY)

When multiple cards appear as siblings on a section background (Flat Section Pattern), they MUST use consistent surface treatment to avoid visual chaos.

### Standard Token Set (MANDATORY)

| Property        | Token                      | Value (Dark)             | Value (Light)           |
| --------------- | -------------------------- | ------------------------ | ----------------------- |
| Background      | `--ob-surface-glass-1`     | `rgba(255,255,255,0.03)` | `rgba(255,255,255,0.4)` |
| Backdrop Filter | `blur(var(--ob-blur-md))`  | 12px                     | 12px                    |
| Border          | `--ob-color-border-subtle` | `rgba(255,255,255,0.08)` | `rgba(0,0,0,0.12)`      |
| Border Radius   | `--ob-radius-sm`           | 4px                      | 4px                     |

### Glass vs Opaque Decision Tree

```
Is the card NESTED inside another card/panel?
├── YES → Use OPAQUE (--ob-color-bg-muted), NO blur
│         Nested blur causes scroll lock
│
└── NO (top-level sibling) → Use GLASS with blur
                             --ob-surface-glass-1 + backdrop-filter
```

### Example CSS

```css
/* ✅ CORRECT - Top-level sibling card with glass + blur */
.my-section__card {
    background: var(--ob-surface-glass-1);
    backdrop-filter: blur(var(--ob-blur-md));
    -webkit-backdrop-filter: blur(var(--ob-blur-md));
    border: 1px solid var(--ob-color-border-subtle);
    border-radius: var(--ob-radius-sm);
    padding: var(--ob-space-150);
}

/* ❌ WRONG - Inconsistent: some cards opaque, some glass */
.card-a {
    background: var(--ob-color-bg-muted);
} /* Opaque */
.card-b {
    background: var(--ob-surface-glass-1);
} /* Glass */
.card-c {
    /* no background */
} /* Transparent */
```

### Fallback for Scroll Performance Issues

If blur causes scroll jank on a specific page:

1. Remove `backdrop-filter` and `-webkit-backdrop-filter`
2. Change background to `--ob-color-bg-muted` (opaque)
3. Document in CSS comment why blur is disabled

---

## Card Interaction States (MANDATORY)

Cards should provide clear visual feedback on interaction. Use **cyan** for hover/focus states to preview the active state and maintain Functional Color Language consistency.

### State Definitions

| State    | Border Color               | Additional Effects                            |
| -------- | -------------------------- | --------------------------------------------- |
| Default  | `--ob-color-border-subtle` | No glow, transparent edge                     |
| Hover    | `--ob-color-neon-cyan`     | Subtle cyan glow (`--ob-glow-neon-cyan-soft`) |
| Focus    | `--ob-color-neon-cyan`     | Glow-bar or border highlight                  |
| Active   | `--ob-color-neon-cyan`     | Full glow-bar + cyan border                   |
| Disabled | `--ob-color-border-subtle` | Reduced opacity (0.5)                         |

### CSS Implementation

```css
/* ✅ CORRECT - Cyan hover for cards */
.my-card {
    border: 1px solid var(--ob-color-border-subtle);
    border-radius: var(--ob-radius-sm);
    transition:
        border-color 0.2s ease,
        box-shadow 0.2s ease;
}

.my-card:hover {
    border-color: var(--ob-color-neon-cyan);
    box-shadow: 0 0 8px var(--ob-color-neon-cyan-muted);
}

.my-card--active,
.my-card:focus-visible {
    border-color: var(--ob-color-neon-cyan);
    box-shadow: 0 0 12px var(--ob-color-neon-cyan-muted);
}

/* ❌ WRONG - Gray/black hover (doesn't preview active state) */
.my-card:hover {
    border-color: var(
        --ob-color-border-default
    ); /* Gray - not aligned with active state */
}
```

### Glow-Bar Pattern (for selection cards)

For cards that represent selectable options (like scenario PATH cards), use a vertical glow-bar on the left edge:

```css
/* Glow-bar container */
.path-card {
    display: flex;
    border: 1px solid var(--ob-color-border-subtle);
}

/* Glow-bar element */
.path-card__glow-bar {
    width: 4px;
    background: transparent;
    transition:
        background 0.2s ease,
        box-shadow 0.2s ease;
}

/* Hover previews glow */
.path-card:hover .path-card__glow-bar {
    background: var(--ob-color-neon-cyan-muted);
}

/* Active/selected shows full glow */
.path-card--active .path-card__glow-bar {
    background: var(--ob-color-neon-cyan);
    box-shadow:
        0 0 8px var(--ob-color-neon-cyan),
        0 0 16px var(--ob-color-neon-cyan-muted);
}
```

### Key Rules

| Rule            | Requirement                                          |
| --------------- | ---------------------------------------------------- |
| Hover color     | MUST use cyan (`--ob-color-neon-cyan`), NOT gray     |
| Hover = preview | Hover state should preview the active/selected state |
| Transition      | Use `transition: 0.2s ease` for smooth feedback      |
| Glow-bar        | Use for selection cards (4px width, left edge)       |
| Focus visible   | Match hover styling for keyboard navigation          |

---

## Tactical Viewport Pattern (Map HUD)

For map-based interfaces, use the **Tactical Viewport** pattern with a HUD overlay displaying real-time telemetry data. This creates a "Live Sensor Feed" aesthetic.

### HUD Corner Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ [LAT/LON]                                      [SYS TIME]       │
│ 1.352083, 103.819836                      2024-01-15 14:32:17  │
│                                                                 │
│                         MAP CONTENT                             │
│                                                                 │
│ [ASSET ID]                                        [STATUS]      │
│ PROP-2024-001                                    ● LIVE         │
└─────────────────────────────────────────────────────────────────┘
```

### Token Usage

| Element        | Token                   | Value                 |
| -------------- | ----------------------- | --------------------- |
| Corner BG      | `--ob-surface-premium`  | Semi-transparent dark |
| Corner Border  | `--ob-border-fine`      | 1px hairline          |
| Corner Radius  | `--ob-radius-xs`        | 2px machined edge     |
| Label Font     | `--ob-font-size-2xs`    | 11px                  |
| Label Tracking | `letter-spacing: 0.1em` | Wide uppercase        |
| Value Font     | `--ob-font-family-mono` | JetBrains Mono        |
| Value Color    | `--ob-color-neon-cyan`  | Cyan telemetry        |
| Status Glow    | `--ob-glow-status-live` | Pulsing indicator     |

### CSS Classes

```css
.map-hud                        /* Container */
.map-hud__corner                /* Corner panel positioning */
.map-hud__corner--top-left      /* Coordinates display */
.map-hud__corner--top-right     /* Timestamp display */
.map-hud__corner--bottom-left   /* Asset ID display */
.map-hud__corner--bottom-right  /* Status indicator */
.map-hud__label                 /* Uppercase label */
.map-hud__value                 /* Monospace value */
.map-hud__status                /* Status with dot */
.map-hud__status--live          /* Cyan pulsing */
.map-hud__status--capturing     /* Amber pulsing */
.map-hud__status--idle          /* Gray static */
```

### Example

```tsx
<PropertyLocationMap
    latitude="1.352083"
    longitude="103.819836"
    propertyId="PROP-2024-001"
    status="live"
    showHud={true}
/>
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

COLORS:     Cyan = brand/selection | Green = success | Red = error | Amber = warning | Indigo = info/AI
```

---

## Pre-Commit Validation

The project includes ESLint rules to catch violations. Run before committing:

```bash
cd frontend && npm run lint
```

---

## Immersive Map Styling Standards

The Unified Capture Page (`/app/capture`) uses an immersive dark map experience that **overrides system theme**.

### Dark Map Configuration (MANDATORY)

| Setting      | Value                             | Rationale                              |
| ------------ | --------------------------------- | -------------------------------------- |
| Mapbox Style | `mapbox://styles/mapbox/dark-v11` | Always dark regardless of system theme |
| Pitch        | `45` degrees                      | 3D perspective for immersion           |
| Zoom         | `16`                              | Street-level detail                    |
| Marker Color | `#3b82f6` (blue-500)              | Visible against dark map               |

### Radar Sweep Animation

During capture/scanning, display a radar sweep animation:

| Token                       | Value                       | Use                    |
| --------------------------- | --------------------------- | ---------------------- |
| `--ob-radar-sweep-color`    | `var(--ob-color-neon-cyan)` | Sweep gradient color   |
| `--ob-radar-sweep-duration` | `4s`                        | Full rotation duration |

```css
/* Radar sweep animation */
.gps-background-map.scanning::before {
    content: '';
    position: absolute;
    inset: 0;
    background: conic-gradient(
        from 0deg,
        transparent 0deg,
        var(--ob-color-neon-cyan) 20deg,
        transparent 40deg
    );
    opacity: 0.3;
    animation: radar-sweep 4s linear infinite;
    pointer-events: none;
    z-index: 1;
}

@keyframes radar-sweep {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}
```

### Glass Card Overlay

Capture form uses glass morphism over the dark map:

| Token      | Value                                | Use                         |
| ---------- | ------------------------------------ | --------------------------- |
| Background | `rgba(20, 20, 20, 0.75)`             | Dark glass surface          |
| Blur       | `var(--ob-blur-xl)` (16px)           | Strong blur for readability |
| Border     | `1px solid rgba(255, 255, 255, 0.1)` | Subtle edge definition      |

### When to Use Immersive vs Standard Map

| Scenario                         | Map Style           | Why                              |
| -------------------------------- | ------------------- | -------------------------------- |
| Capture page (pre-capture)       | Always dark-v11     | Immersive "mission control" feel |
| Property overview (post-capture) | Follow system theme | Standard content context         |
| Finance/analysis pages           | No map needed       | Data-focused                     |

### CSS Classes Reference

| Class                          | Purpose                           |
| ------------------------------ | --------------------------------- |
| `.gps-background-map`          | Full-screen dark Mapbox container |
| `.gps-background-map.scanning` | Activates radar sweep animation   |
| `.capture-card-glass`          | Glass card for capture form       |
| `.gps-hud-card`                | Floating HUD widget cards         |
| `.gps-content-overlay`         | Content layer above map           |

---

## AI Agent Token Checklist

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

**For layout patterns, viewport standards, and architectural decisions, see [UX_ARCHITECTURE.md](./UX_ARCHITECTURE.md)**
