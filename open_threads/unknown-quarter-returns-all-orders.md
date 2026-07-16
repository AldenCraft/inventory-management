# Unknown quarter value returns all orders instead of an empty/error result

**Status:** ✅ Fixed by [#21](https://github.com/AldenCraft/inventory-management/pull/21) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`filter_by_month` handles a `month` value that starts with `Q` only if it is one of the four keys in `QUARTER_MAP` (Q1-2025 … Q4-2025). Any other quarter-shaped value (e.g. `Q5-2025`, `Q1-2024`) matches the `month.startswith('Q')` branch but fails the inner `if month in QUARTER_MAP`, so nothing is returned inside the branch and control falls through to the final `return items`. The caller gets the full, unfiltered list back — silently treating an invalid filter as "no filter".

## Where
- `server/main.py:22-31` — `filter_by_month`; `if month.startswith('Q')` (line 22), inner `if month in QUARTER_MAP` (line 24), and the fall-through `return items` (line 31).
- `server/main.py:144-154` — `/api/orders` calls `filter_by_month` on the filtered orders.

## Repro
`GET /api/orders?month=Q1-2024` (or `?month=Q5-2025`) returns all 250 orders, identical to `GET /api/orders` with no month filter — instead of returning an empty list or a 400 for the unrecognized quarter.

## Fix / acceptance criteria
- When `month.startswith('Q')` but `month not in QUARTER_MAP`, do not fall through to `return items`. Either `return []` for the unrecognized quarter, or `raise HTTPException(status_code=400, detail=...)`.
- An unrecognized quarter must never return the full unfiltered list.
