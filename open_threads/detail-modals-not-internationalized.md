# Detail modals not internationalized (hardcoded English labels)

**Status:** ✅ Fixed by [#36](https://github.com/AldenCraft/inventory-management/pull/36) — merged 2026-07-16

Created: 2026-07-16, from a post-merge review of the inventory-management repo. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
All four detail modals import `t` from `useI18n` but hardcode their user-facing labels in English, so switching the app to Japanese leaves the modals in English. Reusable keys already existed for most labels (`common.close`, `inventory.table.*`, `dashboard.topProducts.*`, `dashboard.inventoryShortages.*`, `finance.monthlyCostFlow.*`, `finance.totalCosts`, `status.*`, `priority.*`, `months.*`); a handful of modal-specific keys were missing. `BacklogDetailModal.vue` additionally rendered a literal `<span class="badge danger">Backordered</span>` and the raw lowercase `{{ backlogItem.priority }}` value.

## Where
- `client/src/components/CostDetailModal.vue` — title `"{month} Cost Breakdown"` (month untranslated), `Total Costs`, `Procurement`/`Operational`/`Labor`/`Overhead`, `% of total`, `Close`.
- `client/src/components/ProductDetailModal.vue` — `Product Details`, `Category`, `Warehouse`, `Units Ordered`, `Total Revenue`, `Current Stock`, `Reorder Point`, `First Order Date`, `Stock Status`, raw `stockLevel` value, `units` suffix, `Close`.
- `client/src/components/InventoryDetailModal.vue` — `Inventory Item Details`, `Quantity on Hand`, `Stock Level`, `vs. reorder point`, `Category`, `Location`, `Reorder Point`, `Units Remaining`, `Unit Cost`, `Total Value`, `Warehouse`, `Status`, `units` suffix, `Close`.
- `client/src/components/BacklogDetailModal.vue` — `Inventory Shortage Details`, `{priority} Priority` (raw lowercase), `Shortage Amount`, `Days Delayed`, `Order ID`, `Item SKU`, `Quantity Needed`, `Quantity Available`, `Status`, hardcoded `Backordered` badge, `units`/`days` suffixes, `Close`.

## Repro
1. Switch the app language to Japanese.
2. Open each detail modal — before the fix the titles, field labels, suffixes, the Backordered badge, and the priority value all stay English.

## Fix / acceptance criteria
- Route every user-facing label through `t()`, reusing existing keys where they exist and translating data values (product `stockLevel` → `status.*` as Dashboard does; backlog `priority` → `priority.*`; the Backordered badge → `status.backordered`; the CostDetailModal month → `months.*` when it maps to a known month, else passthrough for transaction descriptions).
- Add the genuinely missing keys to BOTH `en.js` and `ja.js` in parity (real Japanese): `common.units`, `common.days`, `costDetail.{title,percentOfTotal}`, `productDetail.{title,currentStock,firstOrderDate}`, `inventoryDetail.{title,stockLevel,vsReorderPoint,unitsRemaining}`, `backlogDetail.{title,priorityLabel,shortageAmount,itemSku}`.
- No hardcoded English remains in the four modals; all `t()` keys resolve in both locales; `npm run build` passes.
