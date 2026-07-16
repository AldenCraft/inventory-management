---
name: saas-redesign
description: Redesign a Vue 3 app's UI into a modern SaaS interface — replace a top nav bar with a left vertical sidebar, apply a consistent spacing/layout system, and polish components for a professional look. Use when asked to redesign the UI, modernize/polish the interface, make an app "look like a modern SaaS product", or convert a top nav to a sidebar.
---

# Modern SaaS Redesign (Vue 3)

A reusable playbook for turning a Vue 3 + Vue Router application into a modern
SaaS-style interface: a left vertical navigation sidebar, one consistent spacing
system, and a polished, professional visual pass over the primary surfaces.

**This is a visual redesign, not a rewrite.** Preserve all existing behavior —
routing, state, i18n, filters, modals, API calls. You are changing markup and
styles, not logic.

## Design philosophy

Five principles this skill enforces. Apply all of them.

1. **Left sidebar navigation.** Primary nav lives in a fixed vertical sidebar on
   the left, not a horizontal top bar. Brand at the top, nav items in the middle,
   user/profile area pinned to the bottom.
2. **One spacing scale, used everywhere.** Every margin, padding, and gap comes
   from the scale in `references/design-tokens.md`. Inconsistent, arbitrary
   spacing is the single biggest thing that makes a UI feel unpolished.
3. **Clear visual hierarchy.** Each page reads top-to-bottom: page header
   (title + optional actions) → content cards → detail. Size, weight, and
   spacing signal importance — not color.
4. **Restraint.** Neutral surfaces, one accent color, subtle borders and
   shadows. No gratuitous gradients, heavy shadows, or decorative color.
5. **Structure prescriptive, color adaptive.** The layout, spacing, sidebar, and
   component recipes are fixed (see the token reference). Color is *derived from
   the target app's existing palette* — map the app's current colors onto
   semantic variables rather than replacing the app's identity.

## Scope

**In scope (always do):**
- Convert the top nav to a left vertical sidebar.
- Introduce the token layer (spacing, radius, shadow, type) as CSS variables.
- Add a **collapsible rail toggle** — the sidebar switches between a full
  240px expanded state (icon + label) and a 64px icon-only rail; the choice
  persists across reloads via `localStorage`.
- A component-polish pass on the primary surfaces (cards, tables, buttons, the
  filter bar) for consistent spacing and hierarchy.

**Out of scope (do NOT add unless the user explicitly asks):**
- Responsive / mobile hamburger drawer.
- Dark mode / theme switching.
- Any behavioral or data-model change.

## Tool rules (mandatory in this repo)

- **Delegate every `.vue` create or modify to the `vue-expert` subagent.** This
  is a hard rule in the project's CLAUDE.md. Give the subagent the specific
  component, the tokens to apply, and the recipe from the reference file. Do not
  edit `.vue` files directly.
- **Verify with the Playwright MCP** (`mcp__playwright__*`) against
  `http://localhost:3000`. Load every route and confirm it renders after the
  change.
- **No emojis in UI.** Sidebar and button icons are inline **SVG**, never emoji
  characters (project design-system rule).

## Workflow

Work through these steps in order. Create a todo per step.

### 1. Inventory the app
Find the pieces you'll touch before changing anything:
- The app shell — the component holding the current nav (often `App.vue`).
- The router config (the list of routes = your nav items).
- The views/pages and the shared components (cards, tables, filter bar, modals).
- The **existing color palette** — grep the shell and views for hex values,
  `rgb(...)`, and any existing CSS variables. This is what you'll map onto the
  semantic color variables.

### 2. Extract palette → semantic color variables (adaptive color)
Map the app's current colors onto the semantic variables listed in
`references/design-tokens.md` (`--bg`, `--surface`, `--border`, `--text`,
`--text-muted`, `--primary`, `--primary-hover`, `--sidebar-bg`,
`--sidebar-text`, `--sidebar-active`). Reuse the app's existing hues — do not
invent a new brand color. If the app already uses CSS variables, extend that set.

### 3. Establish the token layer
Add the spacing, radius, shadow, and type-scale variables (from the reference)
to the app shell's root style (e.g. a `:root` block). These become the
vocabulary every component uses from here on.

### 4. Build the layout shell
Restructure the shell into a sidebar + main region:
- A fixed-width sidebar column on the left and a scrollable main content column
  on the right.
- Move the brand/logo into the sidebar top; remove the horizontal top nav.
- Keep the existing `<router-view>` and any always-on components (e.g. a filter
  bar) inside the main region.

### 5. Build the sidebar
Follow the sidebar recipe in the reference:
- Brand block at top.
- Nav items generated from the routes: inline SVG icon + label, with a clear
  **active state** driven by the current route.
- Profile / user area pinned to the bottom.
- **Rail toggle:** a control that switches expanded (240px) ↔ rail (64px). In
  rail mode show icons only (label hidden, tooltip optional). Persist the state
  in `localStorage` and restore it on load.

### 6. Page-header pattern + spacing pass
Give each view a consistent page header (title, optional subtitle/actions) and
apply the spacing scale to the main content padding and the gaps between
sections. Every view should share the same outer rhythm.

### 7. Component polish pass
Apply the card, table, button, and filter-bar recipes from the reference so
spacing, borders, radius, and typography are consistent across surfaces. Aim for
uniformity, not novelty.

### 8. Verify
- Start the app (`./scripts/start.sh` or the project's dev command).
- With the Playwright MCP, visit **every route** and confirm it renders with no
  console errors and no broken layout.
- Toggle the rail and reload to confirm the collapsed/expanded state persists.
- Spot-check that existing behavior still works (filters apply, modals open,
  i18n switching, profile menu).

## Done checklist

- [ ] Top nav removed; left vertical sidebar in its place.
- [ ] Brand at sidebar top, nav items with SVG icons + active state, profile
      pinned at bottom.
- [ ] Rail toggle works and persists across reloads.
- [ ] Spacing / radius / shadow / type tokens defined and used throughout.
- [ ] Color variables derived from the app's existing palette (identity kept).
- [ ] Consistent page-header pattern across all views.
- [ ] Cards, tables, buttons, and filter bar pass the polish recipes.
- [ ] All `.vue` changes went through the `vue-expert` subagent.
- [ ] Every route verified in the browser via Playwright MCP; no regressions.
- [ ] No emoji icons anywhere in the UI.

## Reference

Concrete token values and component recipes live in
[references/design-tokens.md](references/design-tokens.md). Read it when you
reach step 2 and keep it open through the component pass.
