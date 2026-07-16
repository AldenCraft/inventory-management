# Remove dead code in Dashboard.vue and Spending.vue

**Status:** ✅ Fixed by [#28](https://github.com/AldenCraft/inventory-management/pull/28) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
Two views carry dead code left over from removed features: computeds and a ~110-line stylesheet for a chart that no longer exists in Dashboard, and an empty watcher, an unused formatter, and an `alert()`-based transaction handler in Spending. It's noise that misleads readers and duplicates a modal that already exists.

## Items
- [ ] `client/src/views/Dashboard.vue:453-480` — `orderTrendData` computed is returned but never referenced in the template; remove it.
- [ ] `client/src/views/Dashboard.vue:482-487` — `maxOrderCount` computed is returned but never used; remove it.
- [ ] `client/src/views/Dashboard.vue:352-357` — `revenueGoalDisplay` computed is returned but never used; remove it.
- [ ] `client/src/views/Dashboard.vue:1001-1075` — the `.line-chart`/`.line-bar*` stylesheet (~110 lines) is for a removed chart; delete it.
- [ ] `client/src/views/Spending.vue:374-376` — `watch([selectedPeriod], () => { /* comment only */ })` does nothing; remove it.
- [ ] `client/src/views/Spending.vue:396-401` — `formatDate` is defined and returned but unused (the template uses `formatDateShort`); remove it.
- [ ] `client/src/views/Spending.vue:450-453` — `handleTransactionClick` uses `alert()` + `console.log` with hardcoded English/`$`, even though a `CostDetailModal` already exists; convert it to the existing modal pattern.

## Suggested approach
Delete the dead computeds, CSS block, empty watcher, and unused function; rewire the transaction click to open the existing `CostDetailModal`.
