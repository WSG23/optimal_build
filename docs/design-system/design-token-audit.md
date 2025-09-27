# Design Token Audit

This snapshot captures the primitives currently hard-coded across the front-end surfaces. It will guide the first pass at extracting shared design tokens.

## Color Primitive Inventory

The `frontend` app relies on a narrow Tailwind-adjacent palette hard-coded in `frontend/src/index.css`:

- Neutrals: `#0F172A`, `#1E293B`, `#334155`, `#475569`, `#64748B`, `#E2E8F0`, `#F8FAFC`, `#FFFFFF`
- Blues: `#1D4ED8`, `#1E3A8A`, `#2563EB`, `#BFDBFE`, `#CBD5F5`, `#EEF2FF`
- Accents: `#15803D` (success), `#B45309` (warning), `#B91C1C` / `#991B1B` (error), `#F1F5F9`, `#FEE2E2`

The `ui-admin` app leans on Tailwind utility classes and inherits Tailwind's default palette rather than hard-coded hex values. Aligning both surfaces on a shared palette will remove duplication and make future theme work easier.

## Typography

- Base font stack: `Inter, system-ui, sans-serif` across both apps.
- Heading hierarchy: `frontend` implements custom font sizes via CSS; `ui-admin` relies on Tailwind defaults.
- Suggested tokens: `font.family.base`, `font.size.heading`, `font.size.body`, `font.weight.bold`, `font.weight.semibold`.

## Spacing & Radii

Common raw spacing values found in `frontend/src/index.css`:

- `0.25rem`, `0.5rem`, `0.75rem`, `1rem`, `1.5rem`, `2rem`, `2.5rem`, `3rem`, `4rem`
- Additional fine-grained gaps (`0.35rem`, `0.65rem`, `0.85rem`, `0.95rem`, `1.25rem`, `1.75rem`)

Border radii appear at `0.75rem`, `1.25rem`, and `1.5rem`.

## Initial Token Set Proposal

| Category | Token | Value (current) | Notes |
| --- | --- | --- | --- |
| `color.surface.default` | `#FFFFFF` | Card backgrounds|
| `color.surface.alt` | `#F8FAFC` | Panels, subtle backgrounds |
| `color.surface.inverse` | `#0F172A` | Sidebar background |
| `color.border.subtle` | `#CBD5F5` | Input borders |
| `color.border.muted` | `#E2E8F0` | Table dividers |
| `color.text.primary` | `#1E293B` | Body copy |
| `color.text.muted` | `#475569` | Secondary text |
| `color.text.inverse` | `#FFFFFF` | On dark backgrounds |
| `color.brand.primary` | `#2563EB` | Primary actions |
| `color.brand.primary-hover` | `#1D4ED8` | Hover/focus |
| `color.info.accent` | `#1E3A8A` | Informational text |
| `color.success.accent` | `#15803D` | Success states |
| `color.warning.accent` | `#B45309` | Warning states |
| `color.error.accent` | `#B91C1C` | Error states |
| `space.025` | `0.25rem` | XS spacing |
| `space.05` | `0.5rem` | SM spacing |
| `space.1` | `1rem` | Base spacing |
| `space.15` | `1.5rem` | LG spacing |
| `space.2` | `2rem` | XL spacing |
| `radius.md` | `0.75rem` | Buttons, inputs |
| `radius.lg` | `1.5rem` | Cards |

This table will evolve, but it provides an initial contract for the shared design tokens package.

## Next Actions

1. Publish the token values as consumable artifacts (CSS variables + TypeScript map).
2. Update `frontend` styles to reference tokens in one vertical slice (Feasibility Wizard).
3. Add developer tooling to discourage new magic numbers once the tokens ship.

## Tooling Added

- `npm run lint:tokens` (within `frontend`) enforces that the Feasibility flow stays free of raw hex values.
- Tailwind in `ui-admin` now maps tokenized colors/radii/weights; migrate page classes from `slate-*` et al. to the new aliases as you touch them.
- Extend the token lint to other modules once they migrate to the shared system.

## Remaining Admin Surfaces

- `ui-admin/src/pages/SourcesPage.tsx`, `ClausesPage.tsx`, and `EntitlementsPage.tsx` still reference the legacy `slate-*`/`emerald-*` palette.
- `ui-admin/src/components/Sidebar.tsx`, `DiffViewer.tsx`, and PDF viewer utilities depend on the same ad-hoc shades.
- Prioritise these modules next so the admin shell fully respects the shared token layer before widening lint coverage.
