# Open Threads — Guide

One line per open thread. Update "last examined" whenever a thread is reviewed. When a thread is resolved (fixed, filed as a GitHub issue/PR, or dropped), remove its line here and write a dated record in `../history/` (`YYYY-MM-DD-<thread-name>.md`: what the thread was, what we did, the outcome) instead of just deleting the file.

Threads dated 2026-07-16 come from a whole-app multi-agent review (four parallel review agents — backend, large views, remaining views + components, cross-cutting) run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

**Status** column tracks the lifecycle stage. Only states that can rest here appear — a merged PR moves the thread to `../history/`, so it never rests as "merged":

- ⚪ `open` — no work started (no issue, no PR). Default.
- 🔨 `in progress` — actively being worked (local), no PR yet.
- 📝 `#NNN issue` — filed as a GitHub issue, no PR yet.
- 🟢 `PR #NNN` — a PR is open for this thread.
- 🟡 `partial` — some PRs merged/addressing it, but the thread isn't fully resolved.

Keep Status in sync in **two places**: this row and the `**Status:**` line at the top of the thread file.

## High-impact bugs

| Thread | Summary | Status | Created | Last examined |
|---|---|---|---|---|
| [tasks-api-endpoints-missing.md](tasks-api-endpoints-missing.md) | The Tasks feature is silently broken — `api.js` calls `/api/tasks*` routes that don't exist in `main.py`; add-task 404s and is swallowed, mock tasks mask it. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [generate-data-stale-schema.md](generate-data-stale-schema.md) | `generate_data.py` regenerates orders in an old schema (warehouses A/B/C, `WDG-*` SKUs) that matches nothing in the committed JSON; running it breaks every filter and SKU join. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [backlog-demand-referential-integrity.md](backlog-demand-referential-integrity.md) | All backlog `order_id`s/SKUs and 8 of 9 demand SKUs are phantom (absent from orders/inventory); a test even hardcodes the bad SKUs as expected. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [donut-chart-wrong-circumference.md](donut-chart-wrong-circumference.md) | Donut segments scaled against 440 while `r=65` → real circumference ≈408; arcs ~8% long, offsets accumulate, segments overlap/wrap. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [spending-currency-symbol-unconverted.md](spending-currency-symbol-unconverted.md) | Spending charts/tables prepend ¥ to raw USD (only the 4 stat cards convert); in JP the same screen reports figures 150× apart. | ⚪ open | 2026-07-16 | 2026-07-16 |

## Medium bugs

| Thread | Summary | Status | Created | Last examined |
|---|---|---|---|---|
| [formatcurrency-null-crash.md](formatcurrency-null-crash.md) | `formatCurrency(null/undefined)` throws TypeError (USD) / emits `¥NaN` (JPY) — no null guard; easy to hit with empty/filtered data. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [app-mutates-computed-task-array.md](app-mutates-computed-task-array.md) | `App.vue` splices/mutates a `computed` task array from `useAuth`; deletions/toggles silently reset on language switch. Violates the repo's own rule. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [api-base-url-hardcoded.md](api-base-url-hardcoded.md) | `api.js` hardcodes `http://localhost:8001/api`; production `npm run build` points at localhost. Should use `import.meta.env`. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [inventory-modal-warehouse-shows-bin.md](inventory-modal-warehouse-shows-bin.md) | InventoryDetailModal "Warehouse" field passes `location` (bin) instead of `warehouse` (city); duplicates the Location row, city never shown. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [cost-flow-chart-hardcoded-scale.md](cost-flow-chart-hardcoded-scale.md) | Spending cost-flow chart divides by a fixed 25K; months over $25K overflow the plot, axis meaningless in JPY. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [spending-revenue-divide-by-zero.md](spending-revenue-divide-by-zero.md) | Empty/filtered revenue → `maxRevenueValue = 0` → `height: NaN%` on revenue bars. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [spending-totals-dont-reconcile.md](spending-totals-dont-reconcile.md) | `spending.json` category percentages sum to 123.6% and don't track amounts; summary totals disagree with the monthly rollup (labor off ~$880K). | ⚪ open | 2026-07-16 | 2026-07-16 |
| [category-revenue-misattributed-multi-item.md](category-revenue-misattributed-multi-item.md) | Orders tagged with only the first item's category; dashboard attributes the whole order value to it → category revenue under- and over-counted. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [spending-utc-month-bucketing.md](spending-utc-month-bucketing.md) | `toISOString().slice(0,7)` buckets by UTC; a local late-in-month date west of UTC lands in the next month. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [backlog-view-no-i18n.md](backlog-view-no-i18n.md) | `Backlog.vue` never imports `useI18n`; whole page stays English in Japanese mode despite existing keys. | ⚪ open | 2026-07-16 | 2026-07-16 |

## Low bugs

| Thread | Summary | Status | Created | Last examined |
|---|---|---|---|---|
| [unknown-quarter-returns-all-orders.md](unknown-quarter-returns-all-orders.md) | `?month=Q1-2024` (not in `QUARTER_MAP`) falls through to return all 250 orders instead of `[]`/400. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [vfor-index-keys.md](vfor-index-keys.md) | `:key="index"` in Reports.vue (3 loops) and the nested order-items loop in Orders.vue; real keys are available. Repo's #1 listed issue. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [warehouse-filter-case-sensitive.md](warehouse-filter-case-sensitive.md) | Warehouse filter uses exact `==` while category/status use `.lower()`; `?warehouse=london` returns nothing. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [dashboard-kpis-ignore-filters.md](dashboard-kpis-ignore-filters.md) | `total_backlog_items` and several Dashboard KPIs (turnover 4.2, avg processing 2.8, deltas) are constant/hardcoded but look live. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [unvalidated-dates-before-formatting.md](unvalidated-dates-before-formatting.md) | Unguarded `new Date()` / `toLocaleDateString('en-US')` across Dashboard/Reports/Orders/modals; latent given null `actual_delivery` in 108/250 orders. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [backlog-modal-expected-date-missing.md](backlog-modal-expected-date-missing.md) | BacklogDetailModal renders `expected_date`, a field that doesn't exist in the data → "Expected Date" always N/A (visible in Dashboard). | ⚪ open | 2026-07-16 | 2026-07-16 |
| [detail-modal-status-badges-hardcoded-english.md](detail-modal-status-badges-hardcoded-english.md) | Detail-modal `getStockStatus` returns literal English while the Inventory table uses `t('status.*')` — same status, two implementations. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [negative-currency-sign-placement.md](negative-currency-sign-placement.md) | `currency.js` renders `$-1,234` / `¥-185,100` instead of `-$1,234` / `-¥185,100`. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [demand-divide-by-zero-and-trend-mismatch.md](demand-divide-by-zero-and-trend-mismatch.md) | Demand.vue divides by `current_demand` unguarded; trend badge (raw data) can disagree with `getChangeColor`'s ±2% classification. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [total-orders-value-not-rounded.md](total-orders-value-not-rounded.md) | `total_orders_value` returns raw float sum while its siblings `round(...,2)` → float artifacts. | ⚪ open | 2026-07-16 | 2026-07-16 |

## Improvements (clustered)

| Thread | Summary | Status | Created | Last examined |
|---|---|---|---|---|
| [modal-and-dropdown-accessibility.md](modal-and-dropdown-accessibility.md) | No modal has escape-to-close, focus trap, scroll-lock, or aria; dropdowns close via racy `@blur + setTimeout`; SVG donut/clickable rows not keyboard-operable. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [extract-shared-composables.md](extract-shared-composables.md) | Extract `useModal` (a11y + shell), `useStockStatus` (threshold logic implemented 3× with drift), `useCurrency` (symbol computed copy-pasted 6×). | ⚪ open | 2026-07-16 | 2026-07-16 |
| [reports-view-rewrite.md](reports-view-rewrite.md) | Reports.vue is the weakest file: Options API + direct axios to a hardcoded URL, zero i18n, ~13 console.logs (per-cell), reinvented utils, O(n²) bar height, ignores the filter bar. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [dead-code-cleanup.md](dead-code-cleanup.md) | Dashboard dead `orderTrendData`/`maxOrderCount`/`revenueGoalDisplay` + ~110 lines of removed-chart CSS; Spending empty watcher, unused `formatDate`, and native `alert()` where a modal exists. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [backend-api-hygiene.md](backend-api-hygiene.md) | CORS `*` + credentials invalid pairing; missing `response_model` on summary/spending/reports; `api.js` has no timeout/retry/interceptor and no `encodeURIComponent` on ids. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [repo-config-hygiene.md](repo-config-hygiene.md) | `uv.lock` caught by broad `*.lock` gitignore glob (kills reproducibility); 2 dev-only vite/esbuild advisories; `.env.example` empty despite `.mcp.json` needing a token. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [backend-test-coverage-gaps.md](backend-test-coverage-gaps.md) | 40 tests pass but shallow: `/api/reports/*` untested, no test asserts a filter reduces results, no referential-integrity or spending-totals test. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [docs-drift.md](docs-drift.md) | README overstates filter support; real endpoints (`/api/*/{id}`, `/api/reports/*`) undocumented while docs describe non-existent `/api/tasks*` routes. | ⚪ open | 2026-07-16 | 2026-07-16 |
| [fake-auth-hardening.md](fake-auth-hardening.md) | `useAuth` is fake (`isAuthenticated = ref(true)`, no route guard, `logout()` is an alert); worth a comment saying so; `getInitials` throws on a space-less name. | ⚪ open | 2026-07-16 | 2026-07-16 |

## Related to existing threads (not filed here)

These review findings overlap work Jay already has open threads for elsewhere — noted here so they aren't re-filed:

- **Restocking tab:** the backend is stubbed but unwired — `PurchaseOrder`/`CreatePurchaseOrderRequest` models exist but there's no POST endpoint, `purchase_orders.json` is `[]`, so `has_purchase_order` is always `False`; `api.js` already has `createPurchaseOrder`/`getPurchaseOrderByBacklogItem` pointing at routes that don't exist. Backlog rows also have no warehouse/category field, so backlog filtering needs a data change.
- **Table sorting:** no sorting infra exists in any view — greenfield for that thread.
