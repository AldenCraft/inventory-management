# Precomputed spending figures don't reconcile with the monthly data

**Status:** ✅ Fixed by [#15](https://github.com/AldenCraft/inventory-management/pull/15) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The precomputed figures in `spending.json` have drifted from the underlying monthly rollup. The `category_spending` percentages sum to 123.6% and don't even track their own amounts (Components has a larger amount than Raw Materials but a smaller percentage). The `spending_summary` totals also disagree with the sum of `monthly_spending`: procurement is off by ~$45K and labor by ~$880K.

## Where
- `server/data/spending.json:98-123` — `category_spending` percentages: 42.5 + 38.8 + 19.0 + 23.3 = 123.6%; Components amount 2,946,000 > Raw Materials 2,562,000 yet 38.8 < 42.5.
- `server/data/spending.json:3` — `total_procurement_cost` 7,370,415 vs monthly sum 7,415,000.
- `server/data/spending.json:5` — `total_labor_cost` 4,959,000 vs monthly sum 5,838,000 (~$880K off).
- Served as-is by `server/main.py` `/api/spending/summary` and `/api/spending/categories`.

## Repro
- `GET /api/spending/categories` → the four `percentage` values total ~124%.
- Compare `GET /api/spending/summary` cards against the monthly cost-flow chart (sum of `monthly_spending`): procurement and labor totals disagree.

## Fix / acceptance criteria
- Derive each category `percentage` as `amount / sum(amounts) * 100` (so they total 100% and track the amounts).
- Derive `spending_summary` totals from `monthly_spending` (in code or at data-generation time) rather than storing separate figures that drift.
---
