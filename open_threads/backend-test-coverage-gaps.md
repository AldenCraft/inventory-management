# Backend tests are shallow — key arithmetic and integrity untested

**Status:** 🟢 Fixed by [#27](https://github.com/AldenCraft/inventory-management/pull/27) — open, held for review

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The 40 backend tests pass but are mostly smoke/structure checks: they assert keys exist, not that values are correct. The two endpoints with the most arithmetic have zero coverage, no test asserts a filter actually changes results, and there is no referential-integrity or totals-reconciliation test — gaps that let several real bugs through (the backlog/demand phantom-SKU bug is even baked into a test as expected output).

## Items
- [ ] `tests/backend/` — `/api/reports/quarterly` (`server/main.py:230`) and `/api/reports/monthly-trends` (`server/main.py:276`) have zero tests, yet they hold the most arithmetic (`avg_order_value`, `fulfillment_rate` division, the `total_orders>0` guard). Add arithmetic tests.
- [ ] `tests/backend/test_dashboard.py:69-76` — `test_dashboard_summary_with_status_filter` only checks the key exists; no test asserts a filter actually reduces results or that filtered sums are correct. Add filter-reduces-results assertions.
- [ ] `tests/backend/test_misc_endpoints.py:77-78` — no referential-integrity test (would have caught the backlog/demand phantom-SKU bug); the demand test instead hardcodes phantom SKUs `SNR-420`/`CTL-330` as expected. Add an integrity test and fix the baked-in expectation.
- [ ] `tests/backend/` — no spending-totals reconciliation test (would have caught the 123.6% / labor-drift bug). Add one.
- [ ] `tests/backend/` — no 404 test for `/api/orders/{id}` and no invalid-input/edge tests (empty filter results, bad month format). Add them.

## Suggested approach
Add arithmetic tests for the reports endpoints, filter-reduces-results assertions, a referential-integrity test, and a spending-totals reconciliation test (use the backend-api-test skill).
