# Spending page shows the ¥ symbol over un-converted USD numbers

**Status:** ✅ Fixed by [#8](https://github.com/AldenCraft/inventory-management/pull/8) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
On the Spending page only the four top stat cards run values through `formatCurrency()` (which multiplies by ~150 for JPY). Everywhere else the template prepends the bare `currencySymbol` to a raw USD number without converting it. So in Japanese mode the stat cards show properly converted yen while the revenue/cost chart, cost-flow chart, category breakdown, and transactions table show `¥9,500` where the real figure is `$9,500` — the same screen reports the yen amount two different ways, off by 150×. The transaction-detail alert additionally hardcodes `$`.

## Where
- `client/src/views/Spending.vue:15,23,28,33` — the four stat cards correctly use `formatCurrency(...)`.
- `client/src/views/Spending.vue:50-54` — revenue chart Y-axis: `{{ currencySymbol }}{{ maxRevenueValue }}K` etc. (raw USD).
- `client/src/views/Spending.vue:59-60` — revenue/cost bar tooltips use `${currencySymbol}${month.revenue.toLocaleString()}` (raw).
- `client/src/views/Spending.vue:83-88, 93-96` — cost-flow Y-axis (hardcoded 25K…0) and stacked-bar tooltips prepend `currencySymbol` to raw values.
- `client/src/views/Spending.vue:115` — category amount: `{{ currencySymbol }}{{ category.amount.toLocaleString() }}` (raw).
- `client/src/views/Spending.vue:157` — transaction amount: `{{ currencySymbol }}{{ transaction.amount.toLocaleString() }}` (raw).
- `client/src/views/Spending.vue:452` — transaction-detail `alert(...)` hardcodes `$${transaction.amount.toLocaleString()}`.
- `client/src/views/Spending.vue:378-379` — `formatCurrency` wraps `formatCurrencyUtil(value, currentCurrency.value)`, which is the converter that the rest of the page bypasses.

## Repro
Switch the language/currency to Japanese. The four stat cards show converted ¥ (≈150× the USD value), but the revenue-vs-costs chart, monthly cost-flow chart, category breakdown amounts, and transactions table all display `¥9,500` for a value that is really `$9,500`. Clicking a transaction pops an alert that still shows `$`.

## Fix / acceptance criteria
- Route every money display on the page through `formatCurrency(value)` (i.e. `formatCurrencyUtil(value, currentCurrency.value)`), including chart tooltips, category amounts, transaction amounts, and the detail alert.
- Derive the Y-axis maxima (revenue axis and the hardcoded cost-flow 5K…25K labels) from converted values so the axis scale matches the bars.
- After the fix, no on-screen figure mixes the ¥ symbol with an unconverted USD magnitude.
