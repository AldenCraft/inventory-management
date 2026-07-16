# Currency not converted (¥ over raw USD) in detail modals and Orders/Inventory/Restocking views

**Status:** ✅ Fixed by [#36](https://github.com/AldenCraft/inventory-management/pull/36) + [#33](https://github.com/AldenCraft/inventory-management/pull/33) — merged 2026-07-16

Created: 2026-07-16, from a post-merge review of the inventory-management repo. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`utils/currency.js` `formatCurrency()` multiplies USD by ~150 for JPY and prepends the right symbol. Several places bypass it and instead render `{{ currencySymbol }}{{ value.toLocaleString() / .toFixed(2) }}`, prepending the ¥ symbol to a raw USD magnitude. In Japanese mode these surfaces show figures ~150× smaller than reality, and — worse — off by 150× from the page that opened them (e.g. a Dashboard/Spending card correctly shows converted yen, but the detail modal it opens shows the raw USD number under a ¥ sign). This is the same class of bug already fixed for the Spending page in [#8](https://github.com/AldenCraft/inventory-management/pull/8) (`spending-currency-symbol-unconverted.md`), still present in the four detail modals and three views.

## Where
Detail modals (fixed in this pass):
- `client/src/components/CostDetailModal.vue` — total costs + the four buckets (procurement/operational/labor/overhead).
- `client/src/components/ProductDetailModal.vue` — Total Revenue.
- `client/src/components/InventoryDetailModal.vue` — Unit Cost and Total Value (both 2-decimal).

Views (NOT fixed here — owned by a sibling agent/PR):
- `client/src/views/Orders.vue:56,92,104` — `order.total_value` and per-item `unit_price` prepend `currencySymbol` to raw USD.
- `client/src/views/Inventory.vue:63,64` — unit cost and total value (2-decimal) raw.
- `client/src/views/Restocking.vue:10,51,53,61,62` — budget, unit cost, line cost, total cost, remaining — all raw.

## Repro
1. Switch the app to Japanese.
2. Open any of the four detail modals (cost/product/inventory/backlog-adjacent) — before the fix the amounts show the ¥ symbol over the un-converted USD number, contradicting the (correctly converted) figure on the card that opened them.
3. Visit Orders / Inventory / Restocking — same ¥-over-raw-USD mismatch (sibling PR).

## Fix / acceptance criteria
- Route every money value through `formatCurrency(value, currentCurrency.value)` (or `formatCurrencyWithDecimals(value, currentCurrency.value, 2)` where 2 decimals are shown), matching how Dashboard/Spending/Reports already do it. Import `currentCurrency` from `useI18n`; drop the raw `currencySymbol` concatenation.
- After the fix, no on-screen figure mixes the ¥ symbol with an unconverted USD magnitude, and a modal's amounts agree with the page that opened it.
- Modals done in this pass. Remaining acceptance for Orders/Inventory/Restocking tracked to the sibling PR.
