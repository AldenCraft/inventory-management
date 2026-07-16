# Sortable table columns — design

Date: 2026-07-16
Status: approved

## Goal

Make the data tables across the inventory-management client sortable by clicking column
headers.

## Scope

All 7 view tables: Inventory, Orders, Demand, Backlog, Spending, Reports, and the genuine
multi-row data tables on Dashboard. Skip Dashboard summary tables that are only one or two
rows (sorting adds nothing there).

## Behavior

- Click a header cell → sort ascending. Click again → descending. Third click → off,
  which restores the view's existing default order.
- Only one column is sorted at a time.
- The active column shows a small ▲/▼ caret. Inactive columns show no indicator.
- Comparison auto-detects numeric vs string values.

## Architecture

Two shared pieces so sort logic is not copy-pasted into 7 views:

1. `client/src/composables/useTableSort.js`
   - Reactive `sortKey` (string | null) and `sortDir` ('asc' | 'desc' | null).
   - `toggleSort(key)` cycles the clicked column asc → desc → off. Clicking a different
     column starts it at asc.
   - `applySort(rows, accessors)` returns a sorted **copy** of `rows`. When `sortDir` is
     null it returns `rows` unchanged, so each view's existing default ordering is
     preserved for the "off" state.
   - `accessors` is a map `{ columnKey: (row) => value }` so derived columns
     (e.g. Total Value = qty × unit_cost, status rank, i18n text) sort on the intended
     value.

2. `client/src/components/SortableTh.vue`
   - Presentational `<th>`: renders label + caret, emits `sort` with its column key.
   - Props: `columnKey`, `label`, `sortKey`, `sortDir`.
   - Replaces plain `<th>` cells so view templates stay clean.

## Per-view wiring

Each view keeps its current filtered/default-sorted `computed` and wraps the displayed
rows with `applySort(filteredRows, accessors)`. The existing default sort (e.g. Inventory
low-stock-first) becomes the "off" state.

## Design system

Caret in the existing slate palette (#0f172a / #64748b / #e2e8f0). No emojis. Header
hover/cursor affordance consistent with existing table styles.

## Testing

Playwright MCP against http://localhost:3000 — verify a representative table (Inventory)
sorts asc → desc → off, including a derived column (Total Value).

## Process

- Work happens in the `sortable-tables` git worktree.
- All `.vue` creation/edits routed through the `vue-expert` subagent (subproject rule).
- Repo is PUBLIC — no credentials/registry URLs in commits.
