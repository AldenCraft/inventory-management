# Dates parsed/formatted without validation across the app

**Status:** ✅ Fixed by [#23](https://github.com/AldenCraft/inventory-management/pull/23) + [#18](https://github.com/AldenCraft/inventory-management/pull/18) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
Multiple views and components call `new Date(...)` and then format/parse the result without an `isNaN`/validity guard, contradicting the repo date rule ("Validate dates before `.getMonth()` calls" / "validate all external data"). An invalid or missing date string yields "Invalid Date" output, `NaN` sorts, or garbage like "undefined 2024". This is latent today but sits on real data: `actual_delivery` is null in 108 of 250 orders.

## Where
- `client/src/views/Dashboard.vue:635-641` — `formatDate` guards only `!dateString`, then calls `toLocaleDateString` on `new Date(dateString)` without an `isNaN` check (and hardcodes locale selection).
- `client/src/views/Reports.vue:242-252` — `formatMonth` does `monthNames[parseInt(month) - 1]`; bad input produces `"undefined 2024"`.
- `client/src/views/Reports.vue:217` — `formatNumber` calls `num.toString()` with no guard for null/undefined.
- `client/src/views/Orders.vue:115-119` — the sort comparator builds `new Date(a.order_date)` / `new Date(b.order_date)` with no validity guard.
- `client/src/views/Orders.vue:146-154` — `formatDate` calls `new Date(dateString).toLocaleDateString(...)` unconditionally.
- `client/src/components/ProductDetailModal.vue:118` — `toLocaleDateString('en-US', ...)` called after `new Date(dateString)` with only a `!dateString` guard (no `isNaN`; also hardcodes `'en-US'` instead of the current locale).
- `client/src/components/BacklogDetailModal.vue:118` — same pattern as ProductDetailModal.

## Repro
Pass an order/item whose date field is null or malformed (e.g. an order with `actual_delivery: null`, or a `month` string that isn't `YYYY-MM`): the UI shows "Invalid Date", `formatMonth` shows "undefined 2024", and the Orders sort compares `NaN` values yielding an unstable order.

## Fix / acceptance criteria
- Before formatting, validate with `!isNaN(date.getTime())` (and for `formatMonth`, validate the parsed month index) and fall back to a placeholder like `-`/`N/A`.
- In the modals, use the current locale rather than a hardcoded `'en-US'`.
