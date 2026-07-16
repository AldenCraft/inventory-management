# Backend API and client axios hygiene

**Status:** ✅ Fixed by [#29](https://github.com/AldenCraft/inventory-management/pull/29) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The API has several robustness and correctness gaps: a CORS config that is invalid per the spec, several endpoints returning raw dicts/lists with no schema, no validation on query params, and a client axios layer with no timeout/retry/interceptor that interpolates ids into URLs unescaped.

## Items
- [ ] `server/main.py:52-53` — `allow_origins=["*"]` with `allow_credentials=True` is an invalid pairing per the CORS spec (browsers reject a credentialed wildcard; it only works here because the client never sends credentials). Pin explicit origins or drop credentials.
- [ ] `server/main.py:182,210,215,220,225,276` — `/api/dashboard/summary`, `/api/spending/*`, `/api/reports/quarterly`, `/api/reports/monthly-trends`, and `/api/spending/transactions` have no `response_model`, so they return raw dicts/lists with no schema in `/docs`. `transactions.json` (keys `id,date,description,category,warehouse,amount,vendor,type`) has no Pydantic model at all — add one and apply `response_model`.
- [ ] `server/main.py` — no input validation on `month`/`status`/`warehouse`/`category` query params (invalid values silently yield empty or full results); consider `Enum`/`Literal`.
- [ ] `client/src/api.js` — no timeout/retry/interceptor; every method rethrows raw axios errors. Add a single axios instance with a timeout and a response interceptor.
- [ ] `client/src/api.js:15,31,87,92` — `getInventoryItem`/`getOrder`/`deleteTask`/`toggleTask` interpolate ids into the URL without `encodeURIComponent`.

## Suggested approach
Introduce one configured axios instance (timeout + response interceptor) on the client, and server-side add `response_model` to the untyped endpoints plus enum/literal query-param validation.
