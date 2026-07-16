# Negative amounts render with the minus sign after the currency symbol

**Status:** ✅ Fixed by [#19](https://github.com/AldenCraft/inventory-management/pull/19) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The currency formatters build the string by prefixing the symbol to `amount.toLocaleString(...)`. For a negative amount, `toLocaleString` keeps the minus on the number, so the output is `$-1,234` / `¥-185,100` instead of the conventional `-$1,234` / `-¥185,100`. Cosmetic, but wrong anywhere a negative value can appear (refunds, adjustments, negative deltas).

## Where
- `client/src/utils/currency.js:5-12` — `formatCurrency`: `` `¥${...}` `` (line 8) and `` `$${amount.toLocaleString(...)}` `` (line 11).
- `client/src/utils/currency.js:14-21` — `formatCurrencyWithDecimals`: same symbol-then-number construction (lines 17, 20).

## Repro
`formatCurrency(-1234, 'USD')` returns `"$-1,234"`; `formatCurrency(-1234, 'JPY')` returns `"¥-185,100"`. Expected: `"-$1,234"` and `"-¥185,100"`.

## Fix / acceptance criteria
- Detect a negative amount, format the absolute value, and place the minus sign before the currency symbol (e.g. `-$1,234`).
- Applies to both `formatCurrency` and `formatCurrencyWithDecimals`, for USD and JPY.
