# Typography Standards

This document defines the typography standards for the Optimal Build application. All developers should follow these guidelines to ensure consistent font styling across the application.

## Quick Reference

### Font Size Scale

| Token | CSS Variable | Size | Use Case |
|-------|--------------|------|----------|
| `2xs` | `--ob-font-size-2xs` | 11px (0.6875rem) | Smallest readable, timestamps, badges |
| `xs` | `--ob-font-size-xs` | 12px (0.75rem) | Captions, labels, meta text |
| `sm-minus` | `--ob-font-size-sm-minus` | 13px (0.8125rem) | Small body text, compact UI |
| `sm` | `--ob-font-size-sm` | 14px (0.875rem) | Secondary text, descriptions |
| `md` | `--ob-font-size-md` | 15px (0.9375rem) | Enhanced body text |
| `base` | `--ob-font-size-base` | 16px (1rem) | Primary body text |
| `lg` | `--ob-font-size-lg` | 18px (1.125rem) | Section headings, lead text |
| `xl` | `--ob-font-size-xl` | 20px (1.25rem) | Page subtitles |
| `2xl` | `--ob-font-size-2xl` | 24px (1.5rem) | Page titles |
| `3xl` | `--ob-font-size-3xl` | 30px (1.875rem) | Hero headings |
| `4xl` | `--ob-font-size-4xl` | 36px (2.25rem) | Display headings |
| `5xl` | `--ob-font-size-5xl` | 48px (3rem) | Large display |

### Font Weights

| Token | CSS Variable | Weight | Use Case |
|-------|--------------|--------|----------|
| `regular` | `--ob-font-weight-regular` | 400 | Body text, descriptions |
| `medium` | `--ob-font-weight-medium` | 500 | Emphasized text, active states |
| `semibold` | `--ob-font-weight-semibold` | 600 | Labels, buttons, subheadings |
| `bold` | `--ob-font-weight-bold` | 700 | Headings, metrics, emphasis |

### Line Heights

| Token | CSS Variable | Value | Use Case |
|-------|--------------|-------|----------|
| `none` | `--ob-line-height-none` | 1 | Single-line display text |
| `tight` | `--ob-line-height-tight` | 1.2 | Headings, large text |
| `snug` | `--ob-line-height-snug` | 1.4 | Compact lists, cards |
| `normal` | `--ob-line-height-normal` | 1.5 | Standard body text |
| `relaxed` | `--ob-line-height-relaxed` | 1.6 | Long-form content |
| `loose` | `--ob-line-height-loose` | 1.75 | Maximum readability |

### Letter Spacing

| Token | CSS Variable | Value | Use Case |
|-------|--------------|-------|----------|
| `tighter` | `--ob-letter-spacing-tighter` | -0.02em | Display headings (32px+) |
| `tight` | `--ob-letter-spacing-tight` | -0.01em | Subheadings (20-32px) |
| `normal` | `--ob-letter-spacing-normal` | 0 | Body text |
| `wide` | `--ob-letter-spacing-wide` | 0.01em | Small text for readability |
| `wider` | `--ob-letter-spacing-wider` | 0.02em | Buttons, labels |
| `widest` | `--ob-letter-spacing-widest` | 0.05em | Uppercase labels |
| `caps` | `--ob-letter-spacing-caps` | 0.1em | All-caps text |

---

## Usage Guidelines

### Rule 1: Always Use Design Tokens

**Never hardcode font values.** Always use CSS variables or token imports.

```css
/* ❌ WRONG - Hardcoded values */
.my-class {
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

/* ✅ CORRECT - CSS Variables */
.my-class {
  font-size: var(--ob-font-size-sm);
  font-weight: var(--ob-font-weight-semibold);
  letter-spacing: var(--ob-letter-spacing-widest);
}
```

### Rule 2: Map Hardcoded Values to Tokens

When refactoring existing code, use this mapping:

| Hardcoded Value | Use Token |
|-----------------|-----------|
| `0.65rem`, `0.7rem` | `--ob-font-size-2xs` |
| `0.75rem` | `--ob-font-size-xs` |
| `0.8rem`, `0.8125rem` | `--ob-font-size-sm-minus` |
| `0.85rem`, `0.875rem` | `--ob-font-size-sm` |
| `0.9rem`, `0.95rem` | `--ob-font-size-md` |
| `1rem` | `--ob-font-size-base` |
| `fontWeight: 400` | `--ob-font-weight-regular` |
| `fontWeight: 500` | `--ob-font-weight-medium` |
| `fontWeight: 600` | `--ob-font-weight-semibold` |
| `fontWeight: 700` | `--ob-font-weight-bold` |

### Rule 3: Use MUI Typography Variants

In React components with MUI, prefer Typography variants over inline styles:

```tsx
// ❌ WRONG - Inline font styles
<span style={{ fontSize: '0.875rem', fontWeight: 600 }}>
  Label text
</span>

// ✅ CORRECT - MUI Typography variant
<Typography variant="body2" fontWeight={600}>
  Label text
</Typography>

// ✅ ALSO CORRECT - sx prop with tokens
<Typography sx={{
  fontSize: 'var(--ob-font-size-sm)',
  fontWeight: 'var(--ob-font-weight-semibold)'
}}>
  Label text
</Typography>
```

### Rule 4: MUI Typography Variant Guide

| Variant | Font Size | Weight | Use For |
|---------|-----------|--------|---------|
| `h1` | 24px (2xl) | 700 | Page titles |
| `h2` | 20px (xl) | 700 | Section titles |
| `h3` | 18px (lg) | 600 | Card headers |
| `h4` | 16px (base) | 600 | Subsection headers |
| `h5` | 14px (sm) | 600 | Small headers |
| `h6` | 12px (xs) | 600 | Overline headers |
| `body1` | 16px (base) | 400 | Primary body text |
| `body2` | 14px (sm) | 400 | Secondary body text |
| `caption` | 12px (xs) | 400 | Help text, metadata |
| `button` | — | 600 | Button labels |
| `overline` | 12px (xs) | 400 | Category labels (uppercase) |

### Rule 5: Font Families

Only two font families are used:

```css
/* Primary - All UI text */
font-family: var(--ob-font-family-base);
/* 'Inter', system-ui, -apple-system, sans-serif */

/* Code/Technical - Code snippets, monospace data */
font-family: var(--ob-font-family-mono);
/* 'JetBrains Mono', monospace */
```

---

## Component Patterns

### Metric/KPI Display

```tsx
<Box>
  <Typography
    variant="caption"
    sx={{
      letterSpacing: 'var(--ob-letter-spacing-widest)',
      textTransform: 'uppercase',
      color: 'text.secondary'
    }}
  >
    TOTAL REVENUE
  </Typography>
  <Typography
    variant="h3"
    sx={{
      fontFamily: 'var(--ob-font-family-mono)',
      letterSpacing: 'var(--ob-letter-spacing-tight)'
    }}
  >
    $1,234,567
  </Typography>
</Box>
```

### Card Header

```tsx
<Typography
  variant="h4"
  sx={{
    fontWeight: 'var(--ob-font-weight-bold)',
    letterSpacing: 'var(--ob-letter-spacing-tight)'
  }}
>
  Project Overview
</Typography>
<Typography variant="body2" color="text.secondary">
  Last updated 2 hours ago
</Typography>
```

### Table Headers

```css
.table-header {
  font-size: var(--ob-font-size-xs);
  font-weight: var(--ob-font-weight-semibold);
  letter-spacing: var(--ob-letter-spacing-widest);
  text-transform: uppercase;
  color: var(--ob-color-text-secondary);
}
```

### Status Badges

```css
.badge {
  font-size: var(--ob-font-size-2xs);
  font-weight: var(--ob-font-weight-semibold);
  letter-spacing: var(--ob-letter-spacing-wider);
  text-transform: uppercase;
}
```

---

## CSS File Template

When creating new CSS files, start with these base imports:

```css
/* Component styles for [ComponentName]

   Typography tokens used:
   - --ob-font-size-*
   - --ob-font-weight-*
   - --ob-line-height-*
   - --ob-letter-spacing-*
*/

.component-name {
  font-family: var(--ob-font-family-base);
  font-size: var(--ob-font-size-base);
  line-height: var(--ob-line-height-normal);
}

.component-name__heading {
  font-size: var(--ob-font-size-lg);
  font-weight: var(--ob-font-weight-bold);
  letter-spacing: var(--ob-letter-spacing-tight);
  line-height: var(--ob-line-height-tight);
}

.component-name__label {
  font-size: var(--ob-font-size-xs);
  font-weight: var(--ob-font-weight-semibold);
  letter-spacing: var(--ob-letter-spacing-widest);
  text-transform: uppercase;
}

.component-name__body {
  font-size: var(--ob-font-size-sm);
  line-height: var(--ob-line-height-relaxed);
}

.component-name__meta {
  font-size: var(--ob-font-size-xs);
  color: var(--ob-color-text-muted);
}
```

---

## Files Reference

- **Source of Truth**: `core/design-tokens/tokens.css`
- **TypeScript Tokens**: `frontend/src/theme/tokens.ts`
- **MUI Theme**: `frontend/src/theme/theme.ts`

---

## Migration Checklist

When updating a file to use typography tokens:

- [ ] Replace all hardcoded `font-size` values with `var(--ob-font-size-*)`
- [ ] Replace all hardcoded `font-weight` values with `var(--ob-font-weight-*)`
- [ ] Replace all hardcoded `line-height` values with `var(--ob-line-height-*)`
- [ ] Replace all hardcoded `letter-spacing` values with `var(--ob-letter-spacing-*)`
- [ ] Use MUI Typography variants where possible
- [ ] Verify text is readable in both light and dark modes
- [ ] Test at different viewport sizes

---

# Square Cyber-Minimalism Design System

## Overview

The UI uses a "Square Cyber-Minimalism" aesthetic with:
- Sharp, geometric components (4px base radius instead of rounded)
- Elegant 1px fine lines at low opacity
- Preserved glassmorphism and shimmer effects
- Consistent tokenized values

## Border Radius Scale

| Token | Value | Use Case |
|-------|-------|----------|
| `--ob-radius-none` | 0px | Tables, data grids |
| `--ob-radius-xs` | 2px | Buttons, tags, chips |
| `--ob-radius-sm` | 4px | Cards, panels, tiles |
| `--ob-radius-md` | 6px | Inputs, select boxes |
| `--ob-radius-lg` | 8px | Modals/windows ONLY |
| `--ob-radius-pill` | 9999px | Avatars ONLY |

## Fine Line Borders

| Token | Opacity | Use Case |
|-------|---------|----------|
| `--ob-border-fine` | 8% | Default container borders |
| `--ob-border-fine-strong` | 12% | Elevated elements, headers |
| `--ob-border-fine-hover` | 18% | Hover states |
| `--ob-divider` | 6% | Section dividers |
| `--ob-divider-strong` | 10% | Strong dividers |

## Glow Effects

| Token | Intensity | Use Case |
|-------|-----------|----------|
| `--ob-glow-brand-subtle` | 15% | Subtle highlights |
| `--ob-glow-brand-medium` | 25% | Button hover states |
| `--ob-glow-brand-strong` | 40% | Focus/active states |
| `--ob-glow-gold` | 25% | Premium highlights |
| `--ob-glow-success/error/warning` | 20% | Status indicators |

## Canonical Components

Import from `@/components/canonical`:

```tsx
// Containers
import { Card, Panel, Window, DataBlock } from '@/components/canonical'

// Actions
import { Button, Tag, StatusChip } from '@/components/canonical'

// Data display
import { MetricTile, Tabs, TabPanel } from '@/components/canonical'

// Forms
import { Input } from '@/components/canonical'

// Feedback
import { EmptyState, AlertBlock, Skeleton } from '@/components/canonical'
```

## Component Radius Summary

| Component | Border Radius |
|-----------|---------------|
| `Card` | 4px (sm) |
| `Panel` | 4px (sm) |
| `MetricTile` | 4px (sm) |
| `Input` | 4px (sm) |
| `EmptyState` | 4px (sm) |
| `AlertBlock` | 4px (sm) |
| `Button` | 2px (xs) |
| `Tag` | 2px (xs) |
| `StatusChip` | 2px (xs) |
| `Window` | 8px (lg) - ONLY lg radius |
| `DataBlock` | 0px (none) - Hard edges |

## CSS Utility Classes

```css
/* Glass surfaces */
.glass-panel        /* Standard glass (4px) */
.glass-panel-heavy  /* Heavy glass (4px) */
.glass-card         /* Card glass (4px) */
.glass-window       /* Window glass (8px) */

/* Borders */
.border-fine        /* Fine line */
.border-fine-strong /* Strong fine line */
.divider            /* Divider line */

/* Radii */
.radius-none        /* 0px */
.radius-xs          /* 2px */
.radius-sm          /* 4px */
.radius-md          /* 6px */
.radius-lg          /* 8px */

/* Glows */
.glow-primary       /* Brand glow */
.glow-gold          /* Gold glow */

/* Animations */
.animate-entrance   /* Fade up entrance */
.animate-pulse-glow /* Pulsing glow */
.hover-lift         /* Lift on hover */
```
