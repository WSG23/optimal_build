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
If you use MUI numeric spacing (e.g. `spacing={2}` or `sx={{ p: 2 }}`), it MUST remain token-based via the app theme’s `theme.spacing()` mapping (so you still get tokenized spacing, not arbitrary pixels).

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
SPACING:    var(--ob-space-XXX)     where XXX = 025|050|075|100|125|150|175|200|250|300|400|500|600|800
RADIUS:     var(--ob-radius-XXX)    where XXX = none|xs|sm|md|lg|pill
FONT SIZE:  var(--ob-font-size-XXX) where XXX = 2xs|xs|sm-minus|sm|md|base|lg|xl|2xl|3xl|4xl|5xl
ICON SIZE:  var(--ob-size-icon-XXX) where XXX = sm|md|lg|xl
BLUR:       var(--ob-blur-XXX)      where XXX = sm|xs|md|xl|lg
Z-INDEX:    var(--ob-z-XXX)         where XXX = base|dropdown|sticky|fixed|modal-backdrop|modal|popover|tooltip
```

---

## AI Agent Checklist

Before submitting UI code changes, verify:

- [ ] No hardcoded pixel values (use `--ob-space-*` or `--ob-size-*`)
- [ ] No hardcoded spacing (`px`/`rem`); prefer `--ob-space-*` or tokenized MUI spacing numbers
- [ ] No hardcoded border-radius (use `--ob-radius-*`)
- [ ] Cards/panels use `--ob-radius-sm` (4px), NOT `--ob-radius-lg`
- [ ] Buttons use `--ob-radius-xs` (2px)
- [ ] Modals/dialogs use `--ob-radius-lg` (8px)
- [ ] No hardcoded colors (use theme or tokens)
- [ ] Using canonical components where available
- [ ] Font sizes use `--ob-font-size-*` tokens
