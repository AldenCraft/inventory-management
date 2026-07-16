# dashboard summary: total_orders_value is not rounded like total_inventory_value

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
In the dashboard summary response, `total_inventory_value` is wrapped in `round(..., 2)` but `total_orders_value` returns the raw `sum(...)`. Floating-point summation of the order totals can produce values with a long fractional tail (e.g. `...0000004`), so the two money fields are formatted inconsistently.

## Where
- `server/main.py:203` — `"total_inventory_value": round(total_inventory_value, 2)`.
- `server/main.py:207` — `"total_orders_value": sum(order["total_value"] for order in filtered_orders)` (no rounding).

## Repro
`GET /api/dashboard/summary` can return `total_orders_value` like `1234567.8900000004` while `total_inventory_value` is a clean 2-decimal number.

## Fix / acceptance criteria
- Wrap the orders total in `round(..., 2)` to match: `"total_orders_value": round(sum(order["total_value"] for order in filtered_orders), 2)`.
