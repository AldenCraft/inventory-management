# Revenue chart divides by zero when there are no orders

**Status:** ✅ Fixed by [#16](https://github.com/AldenCraft/inventory-management/pull/16) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`maxRevenueValue` is `Math.ceil(max / 1000)`. When there are no orders (and no costs), `max` is 0, so `maxRevenueValue` is 0. `getRevenueBarHeight` then computes `value / (maxRevenueValue * 1000) * 100` = `value / 0 * 100` = `NaN`, and the bars get `height: NaN%`.

## Where
- `client/src/views/Spending.vue:343-348` — `maxRevenueValue = computed(() => Math.ceil(max / 1000))` with no floor on `max`.
- `client/src/views/Spending.vue:391-394` — `getRevenueBarHeight(value)` uses `const maxValue = maxRevenueValue.value * 1000; return (value / maxValue) * 100`.

## Repro
1. Load the Spending view with an empty `allOrders` (or select a period/filter that yields zero orders and zero costs).
2. `maxRevenueValue` = 0 → `getRevenueBarHeight` returns `NaN` → bars render with `height: NaN%`.

## Fix / acceptance criteria
- Floor the divisor at 1, e.g. `Math.max(1, Math.ceil(max / 1000))`, matching the guard pattern used elsewhere.
- With zero orders, revenue bars render at 0% height instead of `NaN%`.
---
