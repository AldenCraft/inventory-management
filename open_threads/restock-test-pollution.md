# Restocking tests pollute global state (suite passes only by run order)

**Status:** ✅ Fixed by [#32](https://github.com/AldenCraft/inventory-management/pull/32) — merged 2026-07-16

Created: 2026-07-16, from a post-merge sweep of the inventory-management repo (reviewing the merged Restocking feature against local `main`). File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`tests/backend/test_restocking.py` POSTs restock orders that append to the process-global `main.orders` list (imported once at startup) with no teardown. Those rows persist for the rest of the session, so tests that recompute aggregates from `/api/orders` (e.g. `test_reports.py`, `test_dashboard.py`) can see extra orders depending on which test ran first. The suite currently passes only because pytest happens to collect files alphabetically (`test_reports` before `test_restocking`); reorder them and reports/dashboard assertions can drift. The task store (`tasks_store` / `_next_task_id`) has the same latent exposure.

## Where
- `server/main.py` — `orders` is a module-global list mutated in place by `create_restocking_order`'s `orders.append(...)`; the `TestClient` shares that process state across every test.
- `tests/backend/test_restocking.py` — `test_submit_restocking_order` and `test_dashboard_kpi_excludes_submitted_restock_order` POST orders with no cleanup.

## Repro
Run the restocking tests before the reports/dashboard tests, e.g.:
`pytest tests/backend/test_restocking.py tests/backend/test_reports.py` — the leaked "Submitted" orders are now visible to later cross-endpoint assertions (before the revenue-exclusion fix, this also inflated report totals).

## Fix / acceptance criteria
- Add an autouse fixture that snapshots and restores `main.orders` (in place), plus `tasks_store` and `_next_task_id` / `_next_restock_seq`, around each mutating test.
- The full backend suite passes regardless of file/test execution order.
