# Several dashboard KPIs look live but ignore the active filters

**Status:** ✅ Fixed by [#21](https://github.com/AldenCraft/inventory-management/pull/21) + [#23](https://github.com/AldenCraft/inventory-management/pull/23) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The dashboard presents several numbers as if they respond to the filter bar, but they are constant or hardcoded. Four of the summary numbers change with warehouse/category/month/status; `total_backlog_items` does not, and several KPI cards are literal values. This makes the dashboard read as "live" while showing static figures, which is misleading once a filter is applied.

## Where
- `server/main.py:200` — `total_backlog_items = len(backlog_items)` is computed from the unfiltered global list, so it never changes with filters. (Backlog rows have no warehouse/category/order_date field, so it cannot be filtered with the current data model — supporting it would require adding those fields, e.g. for a future backlog/restock tab.)
- `client/src/views/Dashboard.vue:18` — Inventory Turnover value `4.2` is a literal.
- `client/src/views/Dashboard.vue:19` — its goal/delta `4.5 (-6.67%)` and the `93.33%` progress width (line 21) are literals.
- `client/src/views/Dashboard.vue:62-65` — Avg Processing Time `2.8`, goal `3.0 (-6.67%)`, and `93.33%` width are literals.
- `client/src/views/Dashboard.vue:340-341` — `ordersData` (`{ fulfilled: 187, goal: 200 }`) and `fillRate` (`96.8`) are hardcoded refs driving the "Orders Fulfilled" and "Order Fill Rate" KPI cards.

## Repro
Change the Warehouse, Category, or Time Period filter. The Inventory Turnover, Avg Processing Time, Orders Fulfilled, and Order Fill Rate KPI cards, plus the "Inventory Shortages" backlog count, stay identical while the other summary figures update.

## Fix / acceptance criteria
- Compute each of these from the filtered data set, or clearly label them as illustrative/static so users don't read them as filter-responsive.
- For `total_backlog_items`: note that filtering it requires adding warehouse/category (and a date) to the backlog data model; until then, label it or document that it is a global count.
