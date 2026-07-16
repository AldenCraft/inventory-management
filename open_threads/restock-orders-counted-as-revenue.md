# Submitted restock orders leak into report revenue

**Status:** ✅ Fixed by [#32](https://github.com/AldenCraft/inventory-management/pull/32) — merged 2026-07-16

Created: 2026-07-16, from a post-merge sweep of the inventory-management repo (reviewing the merged Restocking feature against local `main`). File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
Restock orders are internal procurement, not customer sales, and are stored with `status == "Submitted"`. The dashboard summary already excludes them from its revenue KPI, but the two reporting endpoints sum `total_value` over **all** orders. So once a restock order is submitted, quarterly revenue and month-over-month revenue trends both inflate by the restock's value — and a `2026-07` month bucket appears for procurement spend that isn't revenue at all.

## Where
- `server/main.py:527` — `get_quarterly_reports`: `quarters[quarter]['total_revenue'] += order.get('total_value', 0)` with no status guard.
- `server/main.py:578` — `get_monthly_trends`: `months[month]['revenue'] += order.get('total_value', 0)` with no status guard.
- Contrast `server/main.py` dashboard summary, which already does `if order["status"] != "Submitted"` before summing revenue.

## Repro
1. `GET /api/reports/monthly-trends` — note total revenue and the set of month buckets.
2. `POST /api/restocking/orders` with a valid line item.
3. `GET /api/reports/monthly-trends` again — total revenue is higher and a new bucket for the submit month has appeared. Same for `/api/reports/quarterly`.

## Fix / acceptance criteria
- Skip `status == "Submitted"` orders in both `get_quarterly_reports` and `get_monthly_trends`, mirroring the dashboard summary's exclusion.
- Submitting a restock order leaves monthly-trends revenue (and month buckets) and quarterly revenue unchanged.
