# README / CLAUDE.md have drifted from the actual route surface

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The docs no longer match the real API. The README overstates filter support, both README and root CLAUDE.md omit several endpoints that exist, and the client `api.js` documents endpoints that the backend never implemented. A new dev reading any of these gets a wrong picture of the surface.

## Items
- [ ] `README.md:51` — claims "All endpoints support optional filtering via query params: warehouse, category, status, month", which is false: `/api/inventory` supports only `warehouse`+`category`, and `/api/demand` and `/api/backlog` support none (the root `CLAUDE.md` table is more accurate). Correct the filter-support matrix.
- [ ] `README.md:47-52` and `CLAUDE.md` — omit real endpoints `/api/inventory/{id}`, `/api/orders/{id}`, `/api/reports/quarterly`, `/api/reports/monthly-trends` (all present in `server/main.py`). Document them.
- [ ] `client/src/api.js` — documents `/api/tasks*` and `/api/purchase-orders*` that do not exist server-side; reconcile the client surface with the actual backend (ties to `tasks-api-endpoints-missing`).

## Suggested approach
Correct the filter-support matrix, document the missing endpoints, and reconcile the `api.js` client surface with the real backend routes.
