# Design Tokens & Component Recipes

Concrete values for the SaaS redesign. **Structure (spacing, layout, sidebar,
component recipes) is prescriptive — use these values.** **Color is adaptive —
map the target app's existing palette onto the semantic variables in the Color
section; do not invent a new brand color.**

All tokens are defined once as CSS custom properties on `:root` in the app shell,
then referenced everywhere via `var(--token)`.

## Spacing scale

The only spacing values allowed. Every padding, margin, and gap uses one of these.

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
}
```

Guidance: `--space-2`/`--space-3` inside compact controls; `--space-4` for card
padding and small gaps; `--space-6` between cards and sections; `--space-8`/
`--space-12` for page-level padding and major section breaks.

## Radius, shadow, type

```css
:root {
  /* Radius */
  --radius-sm: 6px;   /* inputs, small controls */
  --radius-md: 8px;   /* buttons, cards */
  --radius-lg: 12px;  /* large panels, modals */

  /* Shadow — keep subtle; two levels only */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  /* Type scale */
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;   /* body default for dense SaaS UIs */
  --text-lg: 16px;
  --text-xl: 20px;
  --text-2xl: 28px;    /* page titles */
  --font-medium: 500;
  --font-semibold: 600;
  --line-tight: 1.3;
  --line-normal: 1.5;
}
```

## Color (adaptive — map from the app's existing palette)

Define these semantic variables and fill them from the target app's current
colors. Example fills below use this app's slate system (`#0f172a`, `#64748b`,
`#e2e8f0`) — **replace with whatever the target app actually uses.**

```css
:root {
  --bg: #f8fafc;              /* app background behind content */
  --surface: #ffffff;        /* cards, sidebar panels, tables */
  --border: #e2e8f0;         /* hairline borders, dividers */
  --text: #0f172a;           /* primary text */
  --text-muted: #64748b;     /* secondary/label text */
  --primary: #2563eb;        /* accent — reuse app's existing accent */
  --primary-hover: #1d4ed8;

  /* Sidebar (can share the neutrals above or use a darker surface) */
  --sidebar-bg: #0f172a;
  --sidebar-text: #cbd5e1;
  --sidebar-text-active: #ffffff;
  --sidebar-active: rgba(255, 255, 255, 0.08);  /* active item background */
}
```

Rules:
- Derive `--primary` from the app's current accent color; do not introduce a new
  hue.
- Keep status colors (success/warn/error) as the app already defines them.
- One accent only. Neutrals carry the rest.

## Layout shell

```
┌──────────┬───────────────────────────────┐
│          │  [main region: scrolls]        │
│ sidebar  │  ┌─────────────────────────┐   │
│ (fixed)  │  │ filter bar (if present)  │   │
│  240px   │  ├─────────────────────────┤   │
│  or      │  │ page header             │   │
│  64px    │  │ content (cards, tables) │   │
│          │  └─────────────────────────┘   │
└──────────┴───────────────────────────────┘
```

```css
.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
  transition: width 0.15s ease;
}
.sidebar.is-rail { width: 64px; }
.main-region {
  flex: 1;
  min-width: 0;          /* prevents flex overflow of wide tables */
  overflow-y: auto;
}
.page {
  padding: var(--space-8);
}
```

## Sidebar recipe

Three vertical zones: brand (top), nav (middle, grows), profile (bottom).

```html
<aside class="sidebar" :class="{ 'is-rail': isRail }">
  <div class="sidebar-brand"><!-- logo; hide text in rail mode --></div>

  <nav class="sidebar-nav">
    <!-- one per route -->
    <router-link class="nav-item" :class="{ active: isActive }" to="...">
      <span class="nav-icon"><!-- inline SVG, 20x20 --></span>
      <span class="nav-label">Label</span>   <!-- hidden in rail mode -->
    </router-link>
  </nav>

  <div class="sidebar-footer">
    <!-- profile / user area, pinned to bottom -->
    <button class="rail-toggle" @click="toggleRail"><!-- SVG chevron --></button>
  </div>
</aside>
```

```css
.sidebar-nav { flex: 1; padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-1); }
.nav-item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--sidebar-text);
  font-size: var(--text-base); font-weight: var(--font-medium);
  text-decoration: none; white-space: nowrap;
}
.nav-item:hover { background: var(--sidebar-active); }
.nav-item.active { background: var(--sidebar-active); color: var(--sidebar-text-active); }
.nav-icon { flex-shrink: 0; width: 20px; height: 20px; display: grid; place-items: center; }
.sidebar.is-rail .nav-label { display: none; }
.sidebar.is-rail .nav-item { justify-content: center; padding: var(--space-2); }
.sidebar-footer { padding: var(--space-3); border-top: 1px solid rgba(255,255,255,0.08); }
```

Rail toggle state — persist and restore:

```js
import { ref } from 'vue'
const isRail = ref(localStorage.getItem('sidebar-rail') === '1')
function toggleRail() {
  isRail.value = !isRail.value
  localStorage.setItem('sidebar-rail', isRail.value ? '1' : '0')
}
```

**Icons:** inline SVG only (no emoji). Use a simple, consistent set — one 20×20
stroke icon per route (e.g. dashboard/grid, box, cart, chart, forecast,
document). Keep `stroke-width` and viewBox consistent across all of them.

## Page header recipe

```html
<header class="page-header">
  <div>
    <h1 class="page-title">Title</h1>
    <p class="page-subtitle">Optional context</p>
  </div>
  <div class="page-actions"><!-- optional buttons --></div>
</header>
```

```css
.page-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: var(--space-4); margin-bottom: var(--space-6);
}
.page-title { font-size: var(--text-2xl); font-weight: var(--font-semibold); color: var(--text); line-height: var(--line-tight); }
.page-subtitle { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--space-1); }
```

## Card recipe

```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}
.card-title { font-size: var(--text-lg); font-weight: var(--font-semibold); color: var(--text); margin-bottom: var(--space-4); }
/* grids of cards */
.card-grid { display: grid; gap: var(--space-6); grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
```

## Table recipe

```css
.table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
.table th {
  text-align: left; padding: var(--space-3) var(--space-4);
  color: var(--text-muted); font-weight: var(--font-semibold);
  text-transform: uppercase; letter-spacing: 0.03em; font-size: var(--text-xs);
  border-bottom: 1px solid var(--border);
}
.table td { padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--border); color: var(--text); }
.table tr:hover td { background: var(--bg); }
```

## Button recipe

```css
.btn {
  display: inline-flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md); border: 1px solid transparent;
  font-size: var(--text-sm); font-weight: var(--font-medium);
  cursor: pointer; line-height: 1;
}
.btn-primary { background: var(--primary); color: #fff; }
.btn-primary:hover { background: var(--primary-hover); }
.btn-secondary { background: var(--surface); color: var(--text); border-color: var(--border); }
.btn-secondary:hover { background: var(--bg); }
```

## Filter bar recipe

Keep it inside the main region, above the page content. Align it to the same
spacing rhythm.

```css
.filter-bar {
  display: flex; flex-wrap: wrap; gap: var(--space-3);
  padding: var(--space-4) var(--space-8);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.filter-bar select, .filter-bar input {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: var(--text-sm); color: var(--text); background: var(--surface);
}
```
