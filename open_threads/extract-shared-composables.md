# Extract shared composables (useModal, useStockStatus, useCurrency)

**Status:** ✅ Fixed by [#30](https://github.com/AldenCraft/inventory-management/pull/30) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
Three pieces of logic are copy-pasted across the client and have already drifted. The six modals each duplicate ~150 lines of overlay/container/header/footer CSS plus the identical close/emit shell; the stock-status thresholds are implemented three times (one hardcoded in English, which caused the untranslated-badge bug); and the currency-symbol computed is pasted across six files. Extracting these removes drift and gives one place to add the accessibility fixes.

## Items
- [ ] `useModal` — the six modals (`InventoryDetailModal.vue`, `BacklogDetailModal.vue`, `CostDetailModal.vue`, `ProductDetailModal.vue`, `ProfileDetailsModal.vue`, `TasksModal.vue`) duplicate the overlay/container/header/footer CSS, the identical `close()`/`emit('close')` pattern, and the Teleport+Transition shell; extract a shared composable and fold escape/scroll-lock/focus-trap in here (see `modal-and-dropdown-accessibility`).
- [ ] `useStockStatus(item)` returning `{key,label,class}` — thresholds (`qty<=reorder`→low; `qty<=reorder*1.5`→adequate; else in-stock) are implemented three times with drift: `client/src/views/Inventory.vue:121-129` (`getStockStatusKey`) and `:178-186` (`getStockStatusClass`), and `client/src/components/InventoryDetailModal.vue:146-172` (hardcoded English labels — the source of the untranslated-badge bug). Consolidate into one composable.
- [ ] `useCurrency` — the `currentCurrency.value === 'JPY' ? '¥' : '$'` computed is copy-pasted in `client/src/views/Inventory.vue:102`, `client/src/views/Orders.vue:93`, `client/src/components/CostDetailModal.vue:105`, `client/src/components/ProductDetailModal.vue:95` (and the remaining modals). Extract one composable.

## Suggested approach
Add three small composables under `client/src/composables/` (`useModal.js`, `useStockStatus.js`, `useCurrency.js`) and replace the duplicated call sites.
