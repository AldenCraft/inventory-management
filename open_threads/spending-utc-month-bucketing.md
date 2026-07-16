# Spending month bucketing uses UTC, misfiling end-of-month dates

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The Spending view derives a `YYYY-MM` month key by doing `new Date(t.date).toISOString().slice(0, 7)`, which converts the parsed date to UTC first. For a local date late on the last day of a month in a timezone west of UTC, the ISO string rolls into the next month, so the transaction/order is bucketed into the wrong month when filtering by period.

## Where
- `client/src/views/Spending.vue:235` — `const transactionMonth = new Date(t.date).toISOString().slice(0, 7)` in `recentTransactions`.
- `client/src/views/Spending.vue:273` — `const orderMonth = new Date(order.order_date).toISOString().slice(0, 7)` in `filteredOrders`.

## Repro
- A transaction dated the last day of a month, parsed in a west-of-UTC local timezone, has its `toISOString()` roll into the following month; filtering by the true period then excludes it (and it appears under the next period instead).

## Fix / acceptance criteria
- Bucket on local date components (`getFullYear()` / `getMonth()`), or compare against the raw `YYYY-MM` substring of the source date string, so the month key doesn't shift with timezone.
---
