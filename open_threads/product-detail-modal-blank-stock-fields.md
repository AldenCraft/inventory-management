# ProductDetailModal shows blank Current Stock / Reorder Point (+ donut/KPI cleanups)

**Status:** ✅ Fixed by [#35](https://github.com/AldenCraft/inventory-management/pull/35) — merged 2026-07-16

Created: 2026-07-16, from a post-merge review of `client/src/views/Dashboard.vue`. File:line references are from local `main` at the time of review and may drift — re-locate before acting.

---

## The problem

Several issues clustered in `client/src/views/Dashboard.vue`:

1. **[MED] Blank "Current Stock" / "Reorder Point" in ProductDetailModal.** The dashboard's
   `topProducts` objects never set `quantityOnHand` / `reorderPoint`, but
   `ProductDetailModal.vue` renders `{{ product.quantityOnHand }} units` and
   `{{ product.reorderPoint }} units`. Clicking a Top Products row opened the modal with
   those two fields blank (`undefined units`), even though the underlying inventory item
   (`invItem`) already carried `quantity_on_hand` / `reorder_point`.

2. **[LOW] Donut center vs arcs disagree once a Submitted restock order exists.** The donut
   center count and `orderHealthMetrics.totalOrders` used `allOrders.length`, but the arcs
   (`statusData`) only count delivered/shipped/processing/backordered. A Submitted restock
   order inflated the center without adding an arc, leaving a visible gap. Separately,
   `fillRate` used `allOrders.length` as its denominator while treating everything except
   backordered as "filled" — so Submitted orders were silently counted as filled.

3. **[a11y] No accessibility on the donut or the clickable table rows.** The order-health
   `<svg>` had no `role`/`title`/`aria-label`, so screen readers announced nothing. The
   Inventory Shortages `<td @click>` cells and the Top Products `<tr @click>` rows were
   mouse-only (inline `cursor: pointer`, no `tabindex`/`role`/keydown), locking out keyboard
   and screen-reader users. (These are the two Dashboard items deferred from thread #30 —
   see `modal-and-dropdown-accessibility.md`.)

4. **[LOW] KPI polish.** The Order Fill Rate progress bar width wasn't clamped (could exceed
   100% and overflow, unlike the other bars). The Avg Processing Time KPI is a
   lower-is-better metric but rendered a growth-style positive/green delta + full green bar
   when *slower* than goal, reading as "good" when it was bad.

## Where

- `client/src/views/Dashboard.vue`, `topProducts` computed — `productMap[sku]` object never set stock fields.
- `client/src/views/Dashboard.vue`, donut `<svg>` + center `<text>`, `statusData` / `orderHealthMetrics.totalOrders` / `fillRate`.
- `client/src/views/Dashboard.vue`, Inventory Shortages `<td @click>` rows + Top Products `<tr @click>` rows.
- `client/src/views/Dashboard.vue`, Order Fill Rate + Avg Processing Time KPI cards.
- `client/src/components/ProductDetailModal.vue` — consumer of `quantityOnHand` / `reorderPoint` (unchanged; strict scope was Dashboard.vue only).

## Fix / acceptance criteria

- [x] Add `quantityOnHand` / `reorderPoint` (from `invItem.quantity_on_hand` / `invItem.reorder_point`, null when no matching inventory item) to each `topProducts` object so the modal shows real numbers. Data trace: inventory JSON (`quantity_on_hand`, `reorder_point`) → `invItem` → `productMap[sku]` → `selectedProduct` → modal.
- [x] Base the donut center count AND the arc scaling on the same four-status sum (`totalOrders` computed), so center = arcs with no gap. Relocated `totalOrders` above its consumers and pointed the center `<text>` at it.
- [x] Exclude Submitted from the fill-rate numerator and denominator by basing `fillRate` on `totalOrders` (four-status sum) instead of `allOrders.length`.
- [x] Donut `<svg>` gets `role="img"`, an `aria-label`, and a `<title>` — both bound to a `donutAriaLabel` computed built from existing i18n keys only (`dashboard.orderHealth.title`, `dashboard.orderHealth.total`, `status.*`).
- [x] Inventory Shortages rows and Top Products rows get `tabindex="0"`, `role="button"`, and `@keydown.enter` / `@keydown.space.prevent` handlers mirroring the click, plus a `:focus-visible` outline.
- [x] Clamp the Order Fill Rate bar width with `Math.min(..., 100)`.
- [x] Invert the Avg Processing Time framing: delta computed as `(goal - actual)/goal` (faster = positive, slower = negative); bar shows goal attainment (`goal/actual`, clamped) and turns amber (`warning`) when slower than goal.

## Verification

- `cd client && npm install && npm run build` passes (123 modules transformed, no errors).
- Confirmed `server/data/inventory.json` items carry `quantity_on_hand` and `reorder_point`, and all i18n keys used by the aria label exist in `client/src/locales/en.js` + `ja.js`.

## Note on thread #30

This work completes the two Dashboard sub-items **deferred from thread #30**
(`modal-and-dropdown-accessibility.md`): the SVG-donut ARIA and the `<td>`/`<tr>` clickable
table-row keyboard operability. The `useCurrency` adoption in `Spending.vue` /
`Restocking.vue` deferred from #30 is unrelated and remains open.

Reused existing i18n keys only; no new locale strings added. Strict scope was
`client/src/views/Dashboard.vue`.
