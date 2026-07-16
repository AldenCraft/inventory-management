# Restocking Tab — Design Spec

**Date:** 2026-07-16
**Branch/worktree:** `restocking-tab` / `wt-restocking-tab`
**Status:** Approved (design), pending spec review

## Goal

Add a **Restocking** tab that lets a user set an available budget with a slider, see
recommended items to restock (drawn from the demand forecast and ranked by trend), and
submit a restocking order. The submitted order appears in the existing **Orders** tab under
a new **Submitted Orders** section that shows delivery lead time.

## Approach

Full-stack, backend-computed. The recommendation logic and order creation live in FastAPI
so they are unit-testable; the frontend is a thin view over two new endpoints. Submitted
restocking orders are appended to the same in-memory `orders` list the Orders tab already
reads, so no separate store is needed. As with all data in this demo, submitted orders
reset when the server restarts (in-memory only).

## Data changes — `server/data/demand_forecasts.json`

Every forecast item gains two fields the feature needs (they don't exist today):

- `unit_cost` (float) — used to price the restock against the budget.
- `lead_time_days` (int) — per-item delivery time; an order's delivery uses the **max**
  across its items.

Concrete values (PSU-501 reuses its real inventory unit cost of 18.99; the rest are
plausible by part type):

| sku | name | current | forecast | trend | unit_cost | lead_time_days | gap | full-gap cost |
|-----|------|--------:|---------:|-------|----------:|---------------:|----:|--------------:|
| WDG-001 | Industrial Widget Type A | 300 | 450 | increasing | 12.50 | 10 | 150 | 1,875.00 |
| BRG-102 | Steel Bearing Assembly | 150 | 152 | stable | 34.00 | 21 | 2 | 68.00 |
| GSK-203 | High-Temperature Gasket | 500 | 600 | increasing | 8.75 | 7 | 100 | 875.00 |
| MTR-304 | Electric Motor 5HP | 50 | 35 | decreasing | 145.00 | 28 | 0 | — |
| FLT-405 | Oil Filter Cartridge | 800 | 950 | increasing | 6.25 | 5 | 150 | 937.50 |
| VLV-506 | Pressure Relief Valve | 120 | 121 | stable | 42.00 | 18 | 1 | 42.00 |
| PSU-501 | 5V 10A Switching Power Supply | 250 | 252 | stable | 18.99 | 14 | 2 | 37.98 |
| SNR-420 | Temperature Sensor Module | 180 | 182 | stable | 27.50 | 12 | 2 | 55.00 |
| CTL-330 | Logic Controller Board | 95 | 96 | stable | 89.00 | 25 | 1 | 89.00 |

`gap = max(0, forecasted_demand − current_demand)`. Total to close every gap ≈ **$3,979.48**.

## Backend — `server/main.py`

### New Pydantic models
- Update `DemandForecast` to include `unit_cost: float` and `lead_time_days: int`.
  Note: this means `GET /api/demand` now returns these two extra fields too. Verified
  harmless — `Demand.vue` only renders `item_name`, `current_demand`, and
  `forecasted_demand` (and computes the change from those two); it never reads
  `unit_cost`/`lead_time_days`, so the Demand tab is unaffected.
- `RestockRecommendation` — `item_sku, item_name, trend, unit_cost, lead_time_days,
  current_demand, forecasted_demand, gap, recommended_quantity, line_cost`.
- `RestockRecommendationsResponse` — `budget, total_cost, remaining_budget,
  recommendations: List[RestockRecommendation]`.
- `RestockOrderLine` (request) — `item_sku, item_name, quantity, unit_cost, lead_time_days`.
- `CreateRestockOrderRequest` — `items: List[RestockOrderLine]`.

### `GET /api/restocking/recommendations?budget=<float>`
1. For each forecast item compute `gap`; drop items with `gap == 0`.
2. Rank by sort key `(trend_rank, -gap, -line_cost)` where
   `trend_rank = {increasing:0, stable:1, decreasing:2}` and `line_cost = gap * unit_cost`.
   Result order for a full budget: WDG-001, FLT-405, GSK-203, BRG-102, SNR-420, PSU-501,
   CTL-330, VLV-506.
3. Greedily take each item's **full gap** while it fits the remaining budget.
4. For the first item that does **not** fully fit, **partial-fill**:
   `recommended_quantity = floor(remaining_budget / unit_cost)`; include it only if `>= 1`,
   then stop.
5. Return recommendations plus `total_cost` and `remaining_budget = budget - total_cost`.

Worked example at `budget=2000`: WDG-001 ×150 ($1,875) fits; FLT-405 full ($937.50) does
not, partial-fill `floor(125/6.25)=20` units ($125.00). Result: WDG-001 ×150 + FLT-405 ×20,
`total_cost=2000.00`, `remaining_budget=0.00`.

Edge cases: `budget<=0` or no positive gaps → empty list, `total_cost=0`.

**Deliberate trade-offs (called out so they aren't mistaken for bugs):**
- *Trend-first ranking is a product choice.* Because `trend_rank` dominates the sort key, a
  stable item with a large gap ranks below an increasing item with a tiny gap — budget is
  intentionally steered toward rising demand first, even if that means smaller absolute
  shortfalls get funded before larger stable ones.
- *Greedy + stop-on-first-miss can leave money unspent.* Once the marginal item is
  partial-filled (or skipped when `<1` unit fits), we stop rather than scanning further for a
  cheaper later item that would still fit. This can leave a non-zero `remaining_budget` even
  though something else was technically affordable. Accepted as a demo-appropriate
  simplification; the `remaining_budget` readout reflects it honestly.

### `POST /api/restocking/orders`
Body: `CreateRestockOrderRequest`. The server builds a real `Order` and **appends it to the
shared `orders` list** (so `GET /api/orders` returns it):
- `id`: `str(len(orders) + 1)`. **Required and non-optional** on the `Order` model
  (`main.py:72`); the existing seed data uses sequential string ids (`"1"`…`"250"`), and
  appending before assigning keeps them unique. Omitting this would fail `response_model`
  validation on the way out and again when the order is re-read via `GET /api/orders`.
- `order_number`: `RST-{year}-####`, where `{year}` is `datetime.now().year` (so it reads
  `RST-2026-…` today, matching `order_date`) and `####` = (count of existing `Submitted`
  orders) + 1, zero-padded to 4.
- `customer`: `"Internal Restock"`.
- `status`: `"Submitted"` (new status value).
- `order_date`: `now = datetime.now()`, stored as `now.isoformat(timespec="seconds")`.
- `expected_delivery`: compute on the datetime first, then format — i.e.
  `(now + timedelta(days=max(lead_time_days over items))).isoformat(timespec="seconds")`.
  (Don't do string + timedelta.)
- `items`: `[{sku, name, quantity, unit_price: unit_cost}]` (matches existing item shape).
- `total_value`: sum of `quantity * unit_cost`.
- `warehouse`/`category`: `None`.
- Returns the created `Order`.

## Frontend — `client/`

All `.vue` creation/significant edits go through the **vue-expert** subagent (repo CLAUDE.md
mandatory rule). `main.js` and `api.js` are plain JS and edited directly.

### `src/api.js`
- `getRestockingRecommendations(budget)` → `GET /api/restocking/recommendations?budget=`.
- `placeRestockingOrder(payload)` → `POST /api/restocking/orders`.

### New view `src/views/Restocking.vue` + route
- Register `/restocking` in `main.js` router; add a **Restocking** nav link in `App.vue`.
- Budget **slider**: `min 0`, `max 5000`, `step 100`, default `2000` (covers the ~$3,980
  total). Show the current budget value next to the slider.
- On slider change (debounced ~250ms) call `getRestockingRecommendations`.
- Recommendations table: item name, sku, trend, unit cost, recommended qty, line cost,
  lead time. Below it: **total cost** and **remaining budget** readout.
- **Place Order** button: disabled when there are no recommendations; on click POSTs the
  picks, shows a success confirmation, and offers a link to the Orders tab. Handle
  loading/error states per the repo's standard pattern.

### `src/views/Orders.vue`

**Filter interaction (resolves the shared-status-filter problem).** `Orders.vue` does not
hold all orders — `loadOrders()` calls `api.getOrders(getCurrentFilters())`, so the server
filters by the global `useFilters` state (`status`, plus warehouse/category/month) and
re-runs on every filter change (`watch`). A client-side `orders.filter(status ===
'Submitted')` would therefore go empty whenever any non-`all` status filter is active, and
submitted orders (which have `warehouse=null`, `category=null`, and a 2026 `order_date`)
would also be dropped by the warehouse/category/month filters. So a single filtered fetch
can't reliably surface them.

**Decision: the Submitted Orders section is independent of the global filter.** It fetches
its own data and is always shown when submitted orders exist:
- Add a second ref + loader, `loadSubmittedOrders()`, that calls
  `api.getOrders({ status: 'Submitted' })` with **only** the status param (ignoring the
  global filters, so it's never hidden by an unrelated warehouse/category/month/status
  selection). Call it in `onMounted` and again after a successful Place Order. It is **not**
  in the filter `watch`, so changing filters never blanks it.
- The existing **All Orders** table keeps using the filtered `orders` ref, but renders
  `orders.filter(o => o.status !== 'Submitted')` so a submitted order never double-lists when
  the status filter is `all`.
- Add a **Submitted Orders** section (card + table) above All Orders, rendered when the
  submitted ref is non-empty. Columns: order number, items, order date, expected delivery,
  **lead time (days)** = `Math.round((new Date(expected_delivery) - new Date(order_date)) /
  86_400_000)`, total value.
- **FilterBar is intentionally left unchanged** — we deliberately do *not* add a "Submitted"
  option to the status dropdown (`FilterBar.vue:48-54`). Restock orders are internal and get
  their own always-visible section; keeping them out of the customer-order status filter
  avoids muddying that control. (Documented here so the omission is a choice, not an oversight.)
- Add a `Submitted` case to `getOrderStatusClass` and a `status.submitted` label. Note the
  `getOrderStatusClass` change is **cosmetic clarity only, not load-bearing**: the function
  already ends in `return statusMap[status] || 'info'` (`Orders.vue:143`), so an unmapped
  `'Submitted'` already resolves to the `info` badge style. We add the explicit entry so the
  intent is visible, not because behavior would otherwise break.

### i18n — `src/locales/en.js` and `src/locales/ja.js`
Add keys: `nav.restocking`, `status.submitted`, and the Restocking view strings
(title, description, budget label, table headers, place-order button, success message) plus
the Orders "Submitted Orders" section header and lead-time column header. Both locales.

## Data flow

Slider change → `Restocking.vue` (debounced) → `api.getRestockingRecommendations(budget)` →
`GET /api/restocking/recommendations` → rank + greedy/partial-fill → JSON → table + totals.
Place Order → `api.placeRestockingOrder(items)` → `POST /api/restocking/orders` → build
Order (with `id`), append to `orders` → returned. Orders tab's independent submitted fetch
(`api.getOrders({status:'Submitted'})`, run on mount and re-run after a submit) → includes
the `Submitted` order → rendered in the Submitted Orders section, regardless of the global
filter state.

## Testing

### pytest — `tests/backend/`
- Recommendations: `budget=0` → empty; `budget=2000` → WDG-001 ×150 + FLT-405 ×20 with
  `total_cost==2000` (verifies greedy + partial-fill + ordering); large budget (e.g. 5000)
  → all positive-gap items, `total_cost≈3979.48`; assert increasing-trend items rank first.
- POST restock order: creates a `Submitted` order; `total_value` = sum of line costs;
  `expected_delivery` = order_date + max lead time; then `GET /api/orders` includes it.

### Playwright (per CLAUDE.md, frontend)
Load `/restocking`, move the slider, confirm the recommendation table + totals update, click
Place Order, navigate to Orders, confirm the order shows in the Submitted Orders section with
a lead-time value.

## Out of scope (YAGNI)
- Editing/removing recommended lines before submitting (take the recommendation as-is).
- Persisting submitted orders across server restarts.
- Budget presets, multi-currency budgeting, or supplier selection.

## Files touched
- `server/data/demand_forecasts.json` (add fields)
- `server/main.py` (models + 2 endpoints + `DemandForecast` update)
- `tests/backend/` (new tests)
- `client/src/main.js` (route)
- `client/src/api.js` (2 methods)
- `client/src/App.vue` (nav — vue-expert)
- `client/src/views/Restocking.vue` (new — vue-expert)
- `client/src/views/Orders.vue` (Submitted section — vue-expert)
- `client/src/locales/en.js`, `client/src/locales/ja.js` (strings)

Intentionally **not** touched: `client/src/components/FilterBar.vue` (no "Submitted" status
option — see the Orders.vue filter-interaction decision above).
