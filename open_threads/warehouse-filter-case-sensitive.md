# Warehouse filter is case-sensitive while category and status are not

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
In `apply_filters`, the warehouse filter uses an exact, case-sensitive `==` comparison, while category and status both lowercase both sides before comparing. This makes warehouse filtering inconsistent with the other filters: a value that differs only in case silently returns nothing.

## Where
- `server/main.py:38-45` — `apply_filters`; warehouse uses `item.get('warehouse') == warehouse` (line 39), whereas category (line 42) and status (line 45) use `.lower()` on both sides.

## Repro
`GET /api/inventory?warehouse=london` returns an empty list even though items exist for warehouse "London", while `GET /api/inventory?category=sensors` correctly matches "Sensors".

## Fix / acceptance criteria
- Make the warehouse comparison case-insensitive, matching the category/status pattern: `item.get('warehouse', '').lower() == warehouse.lower()`.
- `?warehouse=london` returns the same items as `?warehouse=London`.
