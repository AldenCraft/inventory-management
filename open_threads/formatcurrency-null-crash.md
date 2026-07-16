# formatCurrency crashes on null/undefined and returns inconsistent values

**Status:** ✅ Fixed by [#9](https://github.com/AldenCraft/inventory-management/pull/9) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`formatCurrency` has no null/NaN guard on `amount`. The USD path calls `amount.toLocaleString(...)`, which throws a `TypeError` when `amount` is `null` or `undefined`. The JPY path silently produces garbage instead (`¥NaN` for `undefined`, `¥0` for `null`), so the two currencies disagree on the same bad input. Any KPI/summary field that comes back `null` — easy with a filtered or empty dataset — can crash the render.

## Where
- `client/src/utils/currency.js:11` — `return `$${amount.toLocaleString('en-US', { maximumFractionDigits: 0 })}`` with no guard on `amount`.
- `client/src/utils/currency.js:6-8` — JPY branch does `Math.round(amount * USD_TO_JPY)`, which yields `NaN` for `undefined` and `0` for `null`.

## Repro
- `formatCurrency(null, 'USD')` → `TypeError: Cannot read properties of null (reading 'toLocaleString')`
- `formatCurrency(undefined, 'USD')` → `TypeError`
- `formatCurrency(undefined, 'JPY')` → `¥NaN` (`Math.round(undefined * 150)`)
- `formatCurrency(null, 'JPY')` → `¥0` (inconsistent with the USD path crashing)

## Fix / acceptance criteria
- Guard at the top of `formatCurrency` (and the sibling helpers): `if (amount == null || isNaN(amount)) amount = 0`.
- `formatCurrency(null, 'USD')` and `formatCurrency(undefined, 'JPY')` return a stable formatted zero (`$0` / `¥0`) instead of throwing or emitting `NaN`.
- USD and JPY paths behave consistently for the same null/undefined input.
---
