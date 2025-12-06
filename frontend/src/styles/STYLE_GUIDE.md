# Frontend Style Guide

## Canonical CSS Architecture

This document defines the authoritative styling patterns for the Optimal Build frontend.

### Token Hierarchy (Source of Truth)

```
core/design-tokens/tokens.css    ← SINGLE SOURCE OF TRUTH (CSS variables)
        ↓
core/design-tokens/index.ts      ← TypeScript exports for JS/MUI usage
        ↓
styles/core.css                  ← Global resets, base styles
        ↓
styles/app-shell.css             ← App shell layout
        ↓
styles/page-layout.css           ← Shared page patterns
        ↓
styles/[feature].css             ← Feature-specific styles
```

### Rules

1. **Never use inline styles** - All styling must use CSS classes
2. **Never hardcode colors** - Use `var(--ob-color-*)` tokens
3. **Never hardcode spacing** - Use `var(--ob-spacing-*)` tokens
4. **Never hardcode fonts** - Use `var(--ob-font-*)` tokens
5. **Never hardcode radii** - Use `var(--ob-radius-*)` tokens

### Approved Patterns

#### Page Container
```tsx
// ✅ CORRECT
<div className="page">
  <header className="page__header">
    <h1 className="page__title">Page Title</h1>
    <p className="page__subtitle">Description</p>
  </header>
  <section className="page__section">
    <h2 className="page__section-title">Section</h2>
    {/* content */}
  </section>
</div>

// ❌ WRONG - inline styles
<div style={{ padding: '3rem 2rem', maxWidth: '1200px' }}>
```

#### Forms
```tsx
// ✅ CORRECT
<div className="page__form-group">
  <label className="page__label">Label</label>
  <input className="page__input" />
</div>
<button className="page__btn page__btn--primary">Submit</button>

// ❌ WRONG - inline styles on form elements
<input style={{ padding: '0.875rem', border: '1px solid #d2d2d7' }} />
```

#### Cards and Sections
```tsx
// ✅ CORRECT
<div className="page__card">
  <h3 className="page__card-title">Title</h3>
  <p className="page__card-description">Description</p>
</div>

// ❌ WRONG - hardcoded values
<div style={{ background: 'white', borderRadius: '18px', padding: '2rem' }}>
```

#### Alerts
```tsx
// ✅ CORRECT
{error && <div className="page__alert page__alert--error">{error}</div>}

// ❌ WRONG - hardcoded colors
<div style={{ background: '#fff5f5', color: '#d70015' }}>{error}</div>
```

#### Grids
```tsx
// ✅ CORRECT
<div className="page__grid page__grid--3">
  <div className="page__card">...</div>
  <div className="page__card">...</div>
  <div className="page__card">...</div>
</div>

// ❌ WRONG - inline grid styles
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)' }}>
```

### MUI Components

When using MUI components, use theme values:

```tsx
// ✅ CORRECT - uses theme
<Box sx={{ bgcolor: 'background.paper', color: 'text.primary' }}>

// ❌ WRONG - hardcoded colors
<Box sx={{ bgcolor: '#ffffff', color: '#1d1d1f' }}>
```

### Adding New Tokens

1. Add CSS variable to `core/design-tokens/tokens.css`
2. Add TypeScript export to `core/design-tokens/index.ts`
3. Use the variable in your CSS: `var(--ob-new-token)`

### Violations

The following patterns are flagged by the style linter:

- `style={{` in TSX files (inline styles)
- Hardcoded hex colors (`#ffffff`, `#1d1d1f`, etc.)
- Hardcoded pixel values for spacing
- Hardcoded font families
- Direct `px` values for border-radius
