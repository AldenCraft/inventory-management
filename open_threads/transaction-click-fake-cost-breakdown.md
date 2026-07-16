# Spending transaction click shows a misleading fake "Cost Breakdown"

**Status:** 🔨 in progress — fix on branch `worktree-agent-aeefcabea86beb660` (not yet merged)

Created: 2026-07-16, from a post-merge review of the inventory-management repo. File:line references are from the worktree checkout and may drift — re-locate before acting.

---

## The problem
Clicking a row in the Spending view's Recent Transactions table opened the shared `CostDetailModal`, which is built for the four-bucket monthly cost flow (procurement / operational / labor / overhead). `handleTransactionClick` shoehorned a single transaction into that contract by dropping its `amount` into the one bucket matching its category and zeroing the other three. The result was a modal titled "<description> Cost Breakdown" showing one bucket at 100% and three at $0 — a fake breakdown that misrepresents a single transaction as a cost split.

Two related issues in the same view:
- **Revenue counted Submitted restock orders.** `revenueMetrics`, `avgOrderValue`, and the revenue-vs-cost chart built from `api.getOrders()` with no status filter. Submitted orders come from the Restocking flow; their `total_value` is procurement cost, not customer revenue, so including them inflates Total Revenue. The backend already excludes Submitted from dashboard revenue (`server/main.py:466-471`) and `Orders.vue` segregates them into their own card — Spending was the outlier.
- **Month bucketing inconsistency.** `monthlyRevenue` bucketed via `new Date(order.order_date).getMonth()` while the rest of the file uses the timezone-safe `toMonthKey` helper (added by the UTC-bucketing fix, PR #16).
- **Accessibility.** The clickable transaction rows and the click-to-open stacked cost-flow bar were mouse-only (no keyboard operability) — part of thread #30's deferred clickable-row item.

## Where
- `client/src/views/Spending.vue` — `handleTransactionClick` (fake breakdown), `revenueMetrics` / `filteredOrders` / `monthlyRevenue` (revenue + bucketing), the `clickable-row` `<tr>` and the `stacked-bar` `<div>` (a11y).
- `client/src/components/CostDetailModal.vue` — the modal being misused (owned by another agent; not modified here).

## Fix / acceptance criteria
- Transaction click shows an honest, currency-converted transaction detail (description, vendor, date, category, type, amount) — no 100%/$0/$0/$0 fake breakdown. The cost-flow bar click still uses `CostDetailModal` (that path is legitimate).
- Revenue metrics and the revenue chart exclude `status === 'Submitted'` orders.
- `monthlyRevenue` buckets via `toMonthKey` for timezone-safe consistency.
- Transaction rows and the stacked bar are keyboard-operable (tabindex / role / Enter+Space handlers) with visible focus.

## What was done
- Added `client/src/components/TransactionDetailModal.vue` — a small honest detail modal reusing `useModal` (escape / scroll-lock / focus trap) and `formatCurrency`. Reuses existing i18n keys; the "Type" label is hardcoded English because no locale key exists and locale files were out of scope (a `finance.transactions.type` key would localize it).
- `handleTransactionClick` now opens the new modal with the raw transaction; removed the CostDetailModal shoehorn.
- Added a `revenueOrders` computed (excludes Submitted); `filteredOrders` and `monthlyRevenue` build from it. `monthlyRevenue` now buckets via `toMonthKey`.
- Made the transaction rows and stacked bar keyboard-operable (`tabindex="0"`, `role="button"`, Enter/Space handlers, `:focus-visible` outlines).

## Notes / follow-ups
- The static `orders.json` currently has no Submitted orders (they're created at runtime via the Restocking flow), so the revenue exclusion is a correctness/consistency guard that bites once a restock order is submitted in a session.
- A `finance.transactions.type` i18n key (en + ja) would let the transaction "Type" label localize; deferred because this change was scoped to `Spending.vue` + the one new component.
- Inventory.vue's `clickable-row` is still mouse-only — the rest of thread #30's deferred clickable-row a11y work remains for that view.
---
