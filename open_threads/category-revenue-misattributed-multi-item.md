# Multi-item orders attribute all revenue to a single category

**Status:** ✅ Fixed by [#15](https://github.com/AldenCraft/inventory-management/pull/15) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
Data generation tags each order with a single `category` taken from only its first line item (`primary_category`). The backend then filters orders on that one field and attributes the order's entire `total_value` to it. An order that mixes categories is counted as 100% one category and 0% the others, so category revenue is simultaneously over-counted (for the primary) and under-counted (for the rest), and category filters drop orders that legitimately contain that category.

## Where
- `server/generate_data.py:80,87-88` — `primary_category` is set to the first item's category and used as the order's `category`.
- `server/main.py:41-42` — `apply_filters` filters orders on the single `category` field.
- `server/main.py:207` — `get_dashboard_summary` returns `sum(order["total_value"] for order in filtered_orders)`, attributing each order's full value to its one category.

## Repro
An order with a Sensors line and a Controllers line is tagged `category = "Sensors"`.
- `GET /api/dashboard/summary?category=Controllers` drops the order entirely, undercounting Controllers revenue.
- `GET /api/dashboard/summary?category=Sensors` counts 100% of that order's value (including the Controllers line) as Sensors revenue.

## Fix / acceptance criteria
- Attribute revenue per line item (split `total_value` by each item's category), or
- Explicitly document that `category` is order-primary-only and that category revenue is approximate, so the numbers aren't read as exact.
---
