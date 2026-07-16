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

### `POST /api/restocking/orders`
Body: `CreateRestockOrderRequest`. The server builds a real `Order` and **appends it to the
shared `orders` list** (so `GET /api/orders` returns it):
- `order_number`: `RST-2025-####`, where `####` = (count of existing `Submitted` orders)+1,
  zero-padded to 4.
- `customer`: `"Internal Restock"`.
- `status`: `"Submitted"` (new status value).
- `order_date`: `datetime.now().isoformat(timespec="seconds")`.
- `expected_delivery`: `order_date + timedelta(days=max(lead_time_days over items))`.
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
- Split loaded orders: `submittedOrders = orders.filter(o => o.status === 'Submitted')` and
  `otherOrders = orders.filter(o => o.status !== 'Submitted')`. The existing "All Orders"
  table renders `otherOrders` so a submitted order isn't shown twice.
- Add a **Submitted Orders** section (card + table) rendered when `submittedOrders.length`.
  Columns: order number, items, order date, expected delivery, **lead time (days)** =
  round((expected_delivery − order_date) / 1 day), total value.
- Add a `Submitted` case to `getOrderStatusClass` (reuse the `info` styling) and a
  `status.submitted` label.

### i18n — `src/locales/en.js` and `src/locales/ja.js`
Add keys: `nav.restocking`, `status.submitted`, and the Restocking view strings
(title, description, budget label, table headers, place-order button, success message) plus
the Orders "Submitted Orders" section header and lead-time column header. Both locales.

## Data flow

Slider change → `Restocking.vue` (debounced) → `api.getRestockingRecommendations(budget)` →
`GET /api/restocking/recommendations` → rank + greedy/partial-fill → JSON → table + totals.
Place Order → `api.placeRestockingOrder(items)` → `POST /api/restocking/orders` → build
Order, append to `orders` → returned. Orders tab (on next load) → `GET /api/orders` →
includes the `Submitted` order → rendered in the Submitted Orders section.

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
