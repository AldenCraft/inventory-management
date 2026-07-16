# Submitted restock orders crash the warehouse/category/status filters (500)

**Status:** ✅ Fixed by [#32](https://github.com/AldenCraft/inventory-management/pull/32) — merged 2026-07-16

Created: 2026-07-16, from a post-merge sweep of the inventory-management repo (reviewing the merged Restocking feature against local `main`). File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`create_restocking_order` appends a new order with `warehouse: None` and `category: None`. The shared filter helpers then call `.lower()` on those values, but `dict.get(key, default)` returns the stored `None` (the key exists), *not* the default — so `item.get('warehouse', '')` yields `None`, and `None.lower()` raises `AttributeError` → HTTP 500.

Any filtered read hits this once a restock order is in memory: the Orders list, the dashboard summary, and (via `matches_category`) the category filter all crash.

## Where
- `server/main.py` — `create_restocking_order` sets `"warehouse": None` / `"category": None` on the appended order (~line 416).
- `server/main.py:69` — `apply_filters`, warehouse branch `item.get('warehouse', '').lower()` and status branch `item.get('status', '').lower()`.
- `server/main.py:36` — `matches_category`, `item.get('category', '').lower()` and the per-line-item `.lower()`.

## Repro
1. `POST /api/restocking/orders` with a valid line item.
2. `GET /api/orders?warehouse=Tokyo` (or `?category=Sensors`, or `/api/dashboard/summary?warehouse=Tokyo`).
3. Response is 500 (`AttributeError: 'NoneType' object has no attribute 'lower'`).

## Fix / acceptance criteria
- Set the restock order's `warehouse`/`category` to `""` (not `None`) so every order row has the same shape.
- Harden the filters to coerce `None` regardless: `(item.get('warehouse') or '').lower()` in `apply_filters` (warehouse and status branches) and `matches_category` (top-level and per-line).
- A restock submit followed by `?warehouse=`/`?category=`/`?status=` on `/api/orders` and `/api/dashboard/summary` returns 200; the warehouse-filtered list does not include the (warehouse-less) restock order.
