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

NEVER use hardcoded pixel values or MUI spacing numbers. Use design tokens:

| Token            | Value | Use Cases                 |
| ---------------- | ----- | ------------------------- |
| `--ob-space-025` | 2px   | Micro adjustments         |
| `--ob-space-050` | 4px   | Tight spacing, icon gaps  |
| `--ob-space-100` | 8px   | Default component padding |
| `--ob-space-150` | 12px  | Medium spacing            |
| `--ob-space-200` | 16px  | Standard gaps, padding    |
| `--ob-space-300` | 24px  | Section spacing           |
| `--ob-space-400` | 32px  | Large section gaps        |
| `--ob-space-500` | 40px  | Page section dividers     |
| `--ob-space-600` | 48px  | Major sections            |
| `--ob-space-800` | 64px  | Page-level spacing        |

### Examples

```tsx
// ✅ CORRECT - Token-based spacing
<Stack spacing="var(--ob-space-200)">
<Box sx={{ p: 'var(--ob-space-300)', gap: 'var(--ob-space-100)' }}>

// ❌ WRONG - Hardcoded pixel values
<Stack spacing={2}>        // MUI number
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

| Token                | Value    | Use Cases        |
| -------------------- | -------- | ---------------- |
| `--ob-font-size-xs`  | 0.75rem  | Labels, captions |
| `--ob-font-size-sm`  | 0.875rem | Secondary text   |
| `--ob-font-size-md`  | 1rem     | Body text        |
| `--ob-font-size-lg`  | 1.125rem | Subtitles        |
| `--ob-font-size-xl`  | 1.25rem  | Headings         |
| `--ob-font-size-2xl` | 1.5rem   | Large headings   |

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
| `--ob-blur-md` | 12px  | Standard glass effect |
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

| Token             | Value | Use Cases      |
| ----------------- | ----- | -------------- |
| `--ob-z-base`     | 0     | Default        |
| `--ob-z-dropdown` | 100   | Dropdowns      |
| `--ob-z-sticky`   | 200   | Sticky headers |
| `--ob-z-modal`    | 300   | Modals         |
| `--ob-z-tooltip`  | 400   | Tooltips       |

---

## Color Standards

NEVER use hardcoded hex colors. Use:

- MUI theme colors: `theme.palette.primary.main`, `text.primary`, `background.paper`
- Design tokens for brand colors: `var(--ob-brand-500)`, `var(--ob-success-500)`
- Semantic tokens: `var(--ob-color-border-subtle)`, `var(--ob-error-muted)`

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

## Pre-Commit Validation

The project includes ESLint rules to catch violations. Run before committing:

```bash
cd frontend && npm run lint
```

---

## Quick Reference Card

```
SPACING:    var(--ob-space-XXX)     where XXX = 025|050|100|150|200|300|400|500|600|800
RADIUS:     var(--ob-radius-XXX)    where XXX = none|xs|sm|md|lg|pill
FONT SIZE:  var(--ob-font-size-XXX) where XXX = xs|sm|md|lg|xl|2xl
ICON SIZE:  var(--ob-size-icon-XXX) where XXX = sm|md|lg|xl
BLUR:       var(--ob-blur-XXX)      where XXX = sm|md|lg
Z-INDEX:    var(--ob-z-XXX)         where XXX = base|dropdown|sticky|modal|tooltip
```

---

## AI Agent Checklist

Before submitting UI code changes, verify:

- [ ] No hardcoded pixel values (use `--ob-space-*` or `--ob-size-*`)
- [ ] No MUI spacing numbers like `spacing={2}` (use `spacing="var(--ob-space-200)"`)
- [ ] No hardcoded border-radius (use `--ob-radius-*`)
- [ ] Cards/panels use `--ob-radius-sm` (4px), NOT `--ob-radius-lg`
- [ ] Buttons use `--ob-radius-xs` (2px)
- [ ] Modals/dialogs use `--ob-radius-lg` (8px)
- [ ] No hardcoded colors (use theme or tokens)
- [ ] Using canonical components where available
- [ ] Font sizes use `--ob-font-size-*` tokens
