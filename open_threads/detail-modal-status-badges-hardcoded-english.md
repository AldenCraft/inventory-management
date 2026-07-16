# Inventory detail modal stock-status badge is hardcoded English (not translated)

**Status:** ✅ Fixed by [#22](https://github.com/AldenCraft/inventory-management/pull/22) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`InventoryDetailModal`'s `getStockStatus()` returns literal English strings (`'Low Stock'`, `'Adequate'`, `'In Stock'`), so the badge stays in English even when the app is set to Japanese. The Inventory table computes the same status but routes it through `t('status.*')`, so the two surfaces show the same status two different ways — one localized, one not.

## Where
- `client/src/components/InventoryDetailModal.vue:144-153` — `getStockStatus()` returns literal `'Low Stock'` / `'Adequate'` / `'In Stock'`.
- `client/src/views/Inventory.vue:173-176` — `getStockStatus(item)` returns `t(\`status.${key}\`)`, the localized approach.

## Repro
Switch the app to Japanese. The Inventory table shows translated status labels, but opening an item's detail modal shows the status badge still in English.

## Fix / acceptance criteria
- Route the modal badge through `t('status.*')` (existing keys include `status.inStock`, `status.lowStock`, etc.), ideally via the shared stock-status logic (see the extract-shared-composables thread) so table and modal use one implementation.
- Badge text is localized in both surfaces.
