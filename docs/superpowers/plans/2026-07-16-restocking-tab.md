# Restocking Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Restocking tab where a user sets a budget with a slider, sees trend-ranked restock recommendations from the demand forecast, and submits a restocking order that appears in the Orders tab's new Submitted Orders section with delivery lead time.

**Architecture:** Full-stack, backend-computed. Two new FastAPI endpoints (recommendations + submit) hold all logic and are unit-tested with pytest/TestClient. Submitted orders are appended to the same in-memory `orders` list the Orders tab reads. The frontend is a thin Vue 3 view over those endpoints; the Submitted Orders section fetches independently of the global filter.

**Tech Stack:** Python 3.11+ / FastAPI / Pydantic v2 / uvicorn (backend), Vue 3 Composition API / Vue Router / Vite / axios (frontend), pytest + FastAPI TestClient (tests), uv + npm (tooling).

**Spec:** `docs/superpowers/specs/2026-07-16-restocking-tab-design.md`

## Global Constraints

- Repo and any fork are **PUBLIC**: never commit credentials, internal hostnames, or private registry URLs. Leave `client/.npmrc` and the gitignored `client/package-lock.json` in place.
- **Any create/significant-edit of a `.vue` file MUST be delegated to the `vue-expert` subagent** (repo CLAUDE.md mandatory rule). Backend `.py`, `.json`, and `.js` files are edited directly.
- Backend tests live in `tests/backend/`, named `test_<feature>.py`, class `Test<Feature>Endpoints`, using the `client` fixture (see `tests/backend/conftest.py`). Run from `server/` via `uv run pytest ../tests/backend/... -v`.
- Frontend: Composition API only; unique `:key` in `v-for` (never index); validate dates before parsing; no emojis in UI. Design system: slate/gray, status colors green/blue/yellow/red.
- Backend runs on `:8001`, frontend on `:3000`. `api.js` base URL is `http://localhost:8001/api`.
- Recommendation ranking key is `(trend_rank, -gap, -line_cost)` with `trend_rank = {increasing:0, stable:1, decreasing:2}`; greedy full-gap fills, partial-fill the marginal item then stop.

## File Structure

- `server/data/demand_forecasts.json` — add `unit_cost`, `lead_time_days` to all 9 items (Task 1).
- `server/main.py` — extend `DemandForecast`; add recommendation + submit models, `TREND_RANK`, and two endpoints (Tasks 1–3).
- `tests/backend/test_restocking.py` — new test file for both endpoints (Tasks 1–3).
- `client/src/api.js` — two new methods (Task 4).
- `client/src/main.js` — register `/restocking` route (Task 5).
- `client/src/views/Restocking.vue` — new view (Task 5, vue-expert).
- `client/src/App.vue` — nav link (Task 5, vue-expert).
- `client/src/views/Orders.vue` — Submitted Orders section + independent fetch (Task 6, vue-expert).
- `client/src/locales/en.js`, `client/src/locales/ja.js` — strings (Task 7).

---

## Task 0: Worktree setup (dependencies)

**Files:** none (environment only)

- [ ] **Step 1: Install backend deps**

Run:
```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab/server && uv venv && uv sync
```
Expected: venv created, packages synced (fastapi, uvicorn, pydantic, pytest, httpx…).

- [ ] **Step 2: Install frontend deps**

Run:
```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab/client && npm install
```
Expected: `added N packages`.

- [ ] **Step 3: Confirm the existing backend suite is green**

Run:
```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab/server && uv run pytest ../tests/backend -q
```
Expected: `40 passed` (baseline before our changes).

---

## Task 1: Add cost/lead-time to demand data + model

**Files:**
- Modify: `server/data/demand_forecasts.json` (add two fields to all 9 items)
- Modify: `server/main.py` (extend `DemandForecast`, ~lines 84-92)
- Test: `tests/backend/test_restocking.py` (new)

**Interfaces:**
- Produces: each demand-forecast item now has `unit_cost: float` and `lead_time_days: int`, surfaced by `GET /api/demand` and consumed by Task 2's recommendation logic.

- [ ] **Step 1: Write the failing test**

Create `tests/backend/test_restocking.py`:
```python
"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockingEndpoints:
    """Test suite for restocking recommendations and order submission."""

    def test_demand_includes_cost_and_lead_time(self, client):
        """Demand forecast items expose unit_cost and lead_time_days."""
        response = client.get("/api/demand")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        for item in data:
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["lead_time_days"], int)
        wdg = next(i for i in data if i["item_sku"] == "WDG-001")
        assert wdg["unit_cost"] == 12.5
        assert wdg["lead_time_days"] == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd server && uv run pytest ../tests/backend/test_restocking.py::TestRestockingEndpoints::test_demand_includes_cost_and_lead_time -v`
Expected: FAIL — `KeyError: 'unit_cost'` (field not in response; model strips it).

- [ ] **Step 3: Add the two fields to the data file**

Replace the entire contents of `server/data/demand_forecasts.json` with:
```json
[
  { "id": "1", "item_sku": "WDG-001", "item_name": "Industrial Widget Type A", "current_demand": 300, "forecasted_demand": 450, "trend": "increasing", "period": "Next 30 days", "unit_cost": 12.50, "lead_time_days": 10 },
  { "id": "2", "item_sku": "BRG-102", "item_name": "Steel Bearing Assembly", "current_demand": 150, "forecasted_demand": 152, "trend": "stable", "period": "Next 30 days", "unit_cost": 34.00, "lead_time_days": 21 },
  { "id": "3", "item_sku": "GSK-203", "item_name": "High-Temperature Gasket", "current_demand": 500, "forecasted_demand": 600, "trend": "increasing", "period": "Next 30 days", "unit_cost": 8.75, "lead_time_days": 7 },
  { "id": "4", "item_sku": "MTR-304", "item_name": "Electric Motor 5HP", "current_demand": 50, "forecasted_demand": 35, "trend": "decreasing", "period": "Next 30 days", "unit_cost": 145.00, "lead_time_days": 28 },
  { "id": "5", "item_sku": "FLT-405", "item_name": "Oil Filter Cartridge", "current_demand": 800, "forecasted_demand": 950, "trend": "increasing", "period": "Next 30 days", "unit_cost": 6.25, "lead_time_days": 5 },
  { "id": "6", "item_sku": "VLV-506", "item_name": "Pressure Relief Valve", "current_demand": 120, "forecasted_demand": 121, "trend": "stable", "period": "Next 30 days", "unit_cost": 42.00, "lead_time_days": 18 },
  { "id": "7", "item_sku": "PSU-501", "item_name": "5V 10A Switching Power Supply", "current_demand": 250, "forecasted_demand": 252, "trend": "stable", "period": "Next 30 days", "unit_cost": 18.99, "lead_time_days": 14 },
  { "id": "8", "item_sku": "SNR-420", "item_name": "Temperature Sensor Module", "current_demand": 180, "forecasted_demand": 182, "trend": "stable", "period": "Next 30 days", "unit_cost": 27.50, "lead_time_days": 12 },
  { "id": "9", "item_sku": "CTL-330", "item_name": "Logic Controller Board", "current_demand": 95, "forecasted_demand": 96, "trend": "stable", "period": "Next 30 days", "unit_cost": 89.00, "lead_time_days": 25 }
]
```

- [ ] **Step 4: Extend the `DemandForecast` model**

In `server/main.py`, the `DemandForecast` class currently ends with `period: str`. Add two fields so it becomes:
```python
class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
    lead_time_days: int
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd server && uv run pytest ../tests/backend/test_restocking.py -v`
Expected: PASS.

- [ ] **Step 6: Confirm no regressions**

Run: `cd server && uv run pytest ../tests/backend -q`
Expected: `41 passed` (40 baseline + 1 new). Note `Demand.vue` reads only name/current/forecasted, so the extra fields don't affect it.

- [ ] **Step 7: Commit**

```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab
git add server/data/demand_forecasts.json server/main.py tests/backend/test_restocking.py
git commit -m "feat(restocking): add unit_cost and lead_time_days to demand data"
```

---

## Task 2: Recommendations endpoint

**Files:**
- Modify: `server/main.py` (add `math` import, `TREND_RANK`, two Pydantic models, one endpoint)
- Test: `tests/backend/test_restocking.py` (add cases)

**Interfaces:**
- Consumes: `demand_forecasts` (now with `unit_cost`, `lead_time_days`).
- Produces: `GET /api/restocking/recommendations?budget=<float>` → JSON with keys `budget, total_cost, remaining_budget, recommendations[]`; each recommendation has `item_sku, item_name, trend, unit_cost, lead_time_days, current_demand, forecasted_demand, gap, recommended_quantity, line_cost`.

- [ ] **Step 1: Write the failing tests**

Append to the `TestRestockingEndpoints` class in `tests/backend/test_restocking.py`:
```python
    def test_recommendations_zero_budget_is_empty(self, client):
        response = client.get("/api/restocking/recommendations", params={"budget": 0})
        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"] == []
        assert data["total_cost"] == 0

    def test_recommendations_partial_fill_at_2000(self, client):
        """Budget 2000 -> WDG-001 x150 full, FLT-405 x20 partial, spends exactly 2000."""
        response = client.get("/api/restocking/recommendations", params={"budget": 2000})
        data = response.json()
        recs = data["recommendations"]
        assert [r["item_sku"] for r in recs] == ["WDG-001", "FLT-405"]
        assert recs[0]["recommended_quantity"] == 150
        assert recs[0]["line_cost"] == pytest.approx(1875.0)
        assert recs[1]["recommended_quantity"] == 20
        assert recs[1]["line_cost"] == pytest.approx(125.0)
        assert data["total_cost"] == pytest.approx(2000.0)
        assert data["remaining_budget"] == pytest.approx(0.0)

    def test_recommendations_full_budget_covers_all_gaps(self, client):
        response = client.get("/api/restocking/recommendations", params={"budget": 5000})
        data = response.json()
        recs = data["recommendations"]
        # every positive-gap item (8 of 9; the decreasing Motor has no gap)
        assert len(recs) == 8
        assert "MTR-304" not in [r["item_sku"] for r in recs]
        assert data["total_cost"] == pytest.approx(3979.48)
        # increasing-trend items rank ahead of stable ones
        assert recs[0]["item_sku"] == "WDG-001"
        assert [r["trend"] for r in recs[:3]] == ["increasing", "increasing", "increasing"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && uv run pytest ../tests/backend/test_restocking.py -v -k recommendations`
Expected: FAIL with 404 (endpoint not defined) → assertion/JSON errors.

- [ ] **Step 3: Implement the endpoint**

In `server/main.py`: add `import math` near the top imports. After the `DemandForecast` model (or with the other models), add:
```python
TREND_RANK = {"increasing": 0, "stable": 1, "decreasing": 2}


class RestockRecommendation(BaseModel):
    item_sku: str
    item_name: str
    trend: str
    unit_cost: float
    lead_time_days: int
    current_demand: int
    forecasted_demand: int
    gap: int
    recommended_quantity: int
    line_cost: float


class RestockRecommendationsResponse(BaseModel):
    budget: float
    total_cost: float
    remaining_budget: float
    recommendations: List[RestockRecommendation]
```
Then add the endpoint (place it after the existing `/api/demand` route):
```python
@app.get("/api/restocking/recommendations", response_model=RestockRecommendationsResponse)
def get_restocking_recommendations(budget: float = 0):
    """Recommend restock quantities from the demand forecast within a budget.

    Ranks positive-gap items trend-first (increasing > stable > decreasing), then by
    largest unit shortfall, then largest full-gap cost. Greedily buys each item's full
    gap while it fits; partial-fills the first item that doesn't fully fit, then stops
    (a deliberate demo simplification that can leave some budget unspent).
    """
    candidates = []
    for f in demand_forecasts:
        gap = max(0, f["forecasted_demand"] - f["current_demand"])
        if gap == 0:
            continue
        candidates.append({"f": f, "gap": gap, "line_cost": round(gap * f["unit_cost"], 2)})

    candidates.sort(key=lambda c: (TREND_RANK.get(c["f"]["trend"], 99), -c["gap"], -c["line_cost"]))

    recommendations = []
    remaining = budget
    total_cost = 0.0
    for c in candidates:
        f = c["f"]
        full_cost = c["line_cost"]
        if full_cost <= remaining:
            qty = c["gap"]
            cost = full_cost
            partial = False
        else:
            qty = int(remaining // f["unit_cost"])  # whole units that still fit
            if qty < 1:
                break
            cost = round(qty * f["unit_cost"], 2)
            partial = True
        recommendations.append(RestockRecommendation(
            item_sku=f["item_sku"],
            item_name=f["item_name"],
            trend=f["trend"],
            unit_cost=f["unit_cost"],
            lead_time_days=f["lead_time_days"],
            current_demand=f["current_demand"],
            forecasted_demand=f["forecasted_demand"],
            gap=c["gap"],
            recommended_quantity=qty,
            line_cost=cost,
        ))
        total_cost = round(total_cost + cost, 2)
        remaining = round(remaining - cost, 2)
        if partial:
            break

    return RestockRecommendationsResponse(
        budget=round(budget, 2),
        total_cost=total_cost,
        remaining_budget=round(budget - total_cost, 2),
        recommendations=recommendations,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && uv run pytest ../tests/backend/test_restocking.py -v`
Expected: PASS (all recommendation cases green).

- [ ] **Step 5: Commit**

```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab
git add server/main.py tests/backend/test_restocking.py
git commit -m "feat(restocking): add budget recommendations endpoint"
```

---

## Task 3: Submit-order endpoint

**Files:**
- Modify: `server/main.py` (add `datetime`/`timedelta` import, two request models, one POST endpoint)
- Test: `tests/backend/test_restocking.py` (add cases)

**Interfaces:**
- Consumes: request body `{ "items": [{item_sku, item_name, quantity, unit_cost, lead_time_days}, ...] }`.
- Produces: `POST /api/restocking/orders` → the created `Order` (status `"Submitted"`, generated `id`/`order_number`, `expected_delivery` = order_date + max lead time). The order is appended to the shared `orders` list, so `GET /api/orders?status=Submitted` returns it.

- [ ] **Step 1: Write the failing tests**

Append to `TestRestockingEndpoints` in `tests/backend/test_restocking.py`:
```python
    def test_submit_restocking_order(self, client):
        from datetime import datetime
        payload = {"items": [
            {"item_sku": "WDG-001", "item_name": "Industrial Widget Type A",
             "quantity": 150, "unit_cost": 12.5, "lead_time_days": 10},
            {"item_sku": "FLT-405", "item_name": "Oil Filter Cartridge",
             "quantity": 20, "unit_cost": 6.25, "lead_time_days": 5},
        ]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200
        order = response.json()
        assert order["status"] == "Submitted"
        assert order["customer"] == "Internal Restock"
        assert order["order_number"].startswith("RST-")
        assert order["total_value"] == pytest.approx(2000.0)
        assert order["id"]  # non-empty required id
        # max lead time = 10 days
        delta = datetime.fromisoformat(order["expected_delivery"]) - \
            datetime.fromisoformat(order["order_date"])
        assert delta.days == 10
        # it now shows up in the orders list, filterable by status
        submitted = client.get("/api/orders", params={"status": "Submitted"}).json()
        assert any(o["id"] == order["id"] for o in submitted)

    def test_submit_empty_order_rejected(self, client):
        response = client.post("/api/restocking/orders", json={"items": []})
        assert response.status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd server && uv run pytest ../tests/backend/test_restocking.py -v -k submit`
Expected: FAIL with 404/405 (endpoint not defined).

- [ ] **Step 3: Implement the endpoint**

In `server/main.py`: extend the top imports with `from datetime import datetime, timedelta`. Add the request models (near the other models):
```python
class RestockOrderLine(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    lead_time_days: int


class CreateRestockOrderRequest(BaseModel):
    items: List[RestockOrderLine]
```
Add the endpoint (after the recommendations endpoint):
```python
@app.post("/api/restocking/orders", response_model=Order)
def create_restocking_order(request: CreateRestockOrderRequest):
    """Create a restocking order and append it to the in-memory orders list."""
    if not request.items:
        raise HTTPException(status_code=400, detail="No items to order")

    now = datetime.now()
    max_lead = max(line.lead_time_days for line in request.items)
    submitted_count = sum(1 for o in orders if o.get("status") == "Submitted")

    order = {
        "id": str(len(orders) + 1),
        "order_number": f"RST-{now.year}-{submitted_count + 1:04d}",
        "customer": "Internal Restock",
        "items": [
            {"sku": line.item_sku, "name": line.item_name,
             "quantity": line.quantity, "unit_price": line.unit_cost}
            for line in request.items
        ],
        "status": "Submitted",
        "order_date": now.isoformat(timespec="seconds"),
        # compute on the datetime, then format — never string + timedelta
        "expected_delivery": (now + timedelta(days=max_lead)).isoformat(timespec="seconds"),
        "total_value": round(sum(line.quantity * line.unit_cost for line in request.items), 2),
        "actual_delivery": None,
        "warehouse": None,
        "category": None,
    }
    orders.append(order)
    return order
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd server && uv run pytest ../tests/backend/test_restocking.py -v`
Expected: PASS.

- [ ] **Step 5: Confirm full backend suite**

Run: `cd server && uv run pytest ../tests/backend -q`
Expected: all green (baseline 40 + the new restocking tests).

- [ ] **Step 6: Commit**

```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab
git add server/main.py tests/backend/test_restocking.py
git commit -m "feat(restocking): add submit-order endpoint"
```

---

## Task 4: Frontend API client methods

**Files:**
- Modify: `client/src/api.js` (add two methods to the `api` object)

**Interfaces:**
- Consumes: the two backend endpoints from Tasks 2–3.
- Produces: `api.getRestockingRecommendations(budget)` → recommendations response object; `api.placeRestockingOrder(items)` → created order. Used by Tasks 5–6.

- [ ] **Step 1: Add the methods**

In `client/src/api.js`, inside the exported `api` object (e.g. after `getBacklog`), add:
```javascript
  async getRestockingRecommendations(budget) {
    const response = await axios.get(`${API_BASE_URL}/restocking/recommendations`, {
      params: { budget }
    })
    return response.data
  },

  async placeRestockingOrder(items) {
    const response = await axios.post(`${API_BASE_URL}/restocking/orders`, { items })
    return response.data
  },
```

- [ ] **Step 2: Verify against the running backend**

Start the backend, then smoke-test the endpoints the methods call:
```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab/server && uv run python main.py > /tmp/restock-backend.log 2>&1 &
sleep 2
curl -s "http://localhost:8001/api/restocking/recommendations?budget=2000" | python3 -m json.tool
```
Expected: JSON with `total_cost: 2000.0` and two recommendations (WDG-001 x150, FLT-405 x20). Leave the backend running for later tasks (or restart as needed).

- [ ] **Step 3: Commit**

```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab
git add client/src/api.js
git commit -m "feat(restocking): add api client methods"
```

---

## Task 5: Restocking view, route, and nav link

> **Delegate all `.vue` work in this task to the `vue-expert` subagent.** `main.js` is plain JS — edit directly. Give vue-expert this task's requirements and the reference component below; it should match existing view patterns (Composition API `setup()`, `useI18n`, loading/error states, scoped styles, slate/gray design system, no emojis).

**Files:**
- Modify: `client/src/main.js` (import + route)
- Create: `client/src/views/Restocking.vue` (vue-expert)
- Modify: `client/src/App.vue` (nav link — vue-expert)

**Interfaces:**
- Consumes: `api.getRestockingRecommendations`, `api.placeRestockingOrder` (Task 4); i18n keys from Task 7 (`nav.restocking`, `restocking.*`).
- Produces: a `/restocking` route reachable from the top nav.

- [ ] **Step 1: Register the route in `main.js`**

In `client/src/main.js`, add the import alongside the other view imports:
```javascript
import Restocking from './views/Restocking.vue'
```
and add the route to the `routes` array:
```javascript
    { path: '/restocking', component: Restocking },
```

- [ ] **Step 2: Create `Restocking.vue` (vue-expert)**

Create `client/src/views/Restocking.vue`. Reference implementation (vue-expert may refine styling to match the app, but keep the behavior and i18n keys):
```vue
<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <label class="budget-label" for="budget-slider">
        {{ t('restocking.budgetLabel') }}: <strong>{{ currencySymbol }}{{ budget.toLocaleString() }}</strong>
      </label>
      <input
        id="budget-slider"
        type="range"
        min="0"
        max="5000"
        step="100"
        v-model.number="budget"
        class="budget-slider"
      />
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedTitle') }}</h3>
        </div>
        <div v-if="recommendations.length === 0" class="empty">
          {{ t('restocking.empty') }}
        </div>
        <table v-else class="restock-table">
          <thead>
            <tr>
              <th>{{ t('restocking.table.item') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.quantity') }}</th>
              <th>{{ t('restocking.table.lineCost') }}</th>
              <th>{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rec in recommendations" :key="rec.item_sku">
              <td>{{ rec.item_name }}</td>
              <td>{{ rec.trend }}</td>
              <td>{{ currencySymbol }}{{ rec.unit_cost.toFixed(2) }}</td>
              <td>{{ rec.recommended_quantity }}</td>
              <td>{{ currencySymbol }}{{ rec.line_cost.toLocaleString() }}</td>
              <td>{{ t('restocking.days', { count: rec.lead_time_days }) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="restock-summary">
          <span>{{ t('restocking.totalCost') }}: <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong></span>
          <span>{{ t('restocking.remaining') }}: <strong>{{ currencySymbol }}{{ remaining.toLocaleString() }}</strong></span>
        </div>

        <button
          class="place-order-btn"
          :disabled="recommendations.length === 0 || placing"
          @click="placeOrder"
        >
          {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
        <p v-if="successMessage" class="success">
          {{ successMessage }}
          <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currencySymbol } = useI18n()

    const budget = ref(2000)
    const recommendations = ref([])
    const totalCost = ref(0)
    const remaining = ref(0)
    const loading = ref(false)
    const error = ref(null)
    const placing = ref(false)
    const successMessage = ref('')

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockingRecommendations(budget.value)
        recommendations.value = data.recommendations
        totalCost.value = data.total_cost
        remaining.value = data.remaining_budget
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce the slider so we don't fire a request on every pixel of drag.
    watch(budget, () => {
      successMessage.value = ''
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 250)
    })

    const placeOrder = async () => {
      try {
        placing.value = true
        error.value = null
        const items = recommendations.value.map(r => ({
          item_sku: r.item_sku,
          item_name: r.item_name,
          quantity: r.recommended_quantity,
          unit_cost: r.unit_cost,
          lead_time_days: r.lead_time_days
        }))
        const order = await api.placeRestockingOrder(items)
        successMessage.value = t('restocking.success', { orderNumber: order.order_number })
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t, currencySymbol, budget, recommendations, totalCost, remaining,
      loading, error, placing, successMessage, placeOrder
    }
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.budget-card { padding: 1.5rem; margin-bottom: 1.5rem; }
.budget-label { display: block; margin-bottom: 0.75rem; }
.budget-slider { width: 100%; }
.restock-table { width: 100%; border-collapse: collapse; }
.restock-table th, .restock-table td { padding: 0.6rem 0.75rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
.restock-summary { display: flex; gap: 2rem; margin: 1rem 0; }
.place-order-btn { background: #0f172a; color: #fff; border: none; padding: 0.6rem 1.25rem; border-radius: 6px; cursor: pointer; }
.place-order-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.success { color: #16a34a; margin-top: 0.75rem; }
.error { color: #dc2626; }
.empty { color: #64748b; padding: 1rem 0; }
</style>
```

- [ ] **Step 3: Add the nav link in `App.vue` (vue-expert)**

In `client/src/App.vue`, inside `<nav class="nav-tabs">`, add a link after the Demand Forecast link:
```html
          <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
            {{ t('nav.restocking') }}
          </router-link>
```

- [ ] **Step 4: Verify in the browser**

Ensure backend (`:8001`) and frontend (`:3000`) are running (`npm run dev` in `client/`). Load `http://localhost:3000/restocking`. Confirm: the Restocking nav tab appears; the slider defaults to $2,000 and shows WDG-001 ×150 + FLT-405 ×20 with total $2,000 / remaining $0; dragging the slider updates the table. (i18n keys land in Task 7 — until then labels may show raw keys; that's expected.)

- [ ] **Step 5: Commit**

```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab
git add client/src/main.js client/src/views/Restocking.vue client/src/App.vue
git commit -m "feat(restocking): add Restocking view, route, and nav link"
```

---

## Task 6: Orders tab — Submitted Orders section

> **Delegate to the `vue-expert` subagent.** This is a significant modification of `Orders.vue`.

**Files:**
- Modify: `client/src/views/Orders.vue` (independent submitted fetch + section + status class)

**Interfaces:**
- Consumes: `api.getOrders({ status: 'Submitted' })` (existing method); orders created by Task 3.
- Produces: a Submitted Orders section that renders independently of the global filter.

- [ ] **Step 1: Add an independent submitted-orders fetch**

In `Orders.vue`'s `setup()`, add a ref and loader that ignore the global filters (pass only `status: 'Submitted'`), and call it on mount:
```javascript
    const submittedOrders = ref([])

    const loadSubmittedOrders = async () => {
      try {
        // Independent of the global filter so it's never blanked by an unrelated
        // warehouse/category/month/status selection.
        submittedOrders.value = await api.getOrders({ status: 'Submitted' })
      } catch (err) {
        // non-fatal: the main table still renders
        console.error('Failed to load submitted orders:', err)
      }
    }

    onMounted(() => {
      loadOrders()
      loadSubmittedOrders()
    })
```
Remove the existing bare `onMounted(loadOrders)` line so it isn't registered twice. Add `submittedOrders` and a `submittedLeadTime` helper (below) to the `setup()` return object.

- [ ] **Step 2: Exclude submitted orders from the All Orders table**

Where the All Orders table iterates `orders`, filter them out so a submitted order never double-lists when the status filter is `all`. Add a computed:
```javascript
    const otherOrders = computed(() =>
      orders.value.filter(o => o.status !== 'Submitted')
    )
```
Change the All Orders `v-for` to iterate `otherOrders` (and its count label to `otherOrders.length`). Import `computed` from `vue` if not already imported, and return `otherOrders`.

- [ ] **Step 3: Add a lead-time helper**

```javascript
    const submittedLeadTime = (order) => {
      const start = new Date(order.order_date)
      const end = new Date(order.expected_delivery)
      if (isNaN(start.getTime()) || isNaN(end.getTime())) return '-'
      return Math.round((end - start) / 86400000)  // ms per day
    }
```

- [ ] **Step 4: Render the Submitted Orders section**

In the template, above the existing All Orders card, add (rendered only when there are submitted orders):
```html
      <div class="card" v-if="submittedOrders.length">
        <div class="card-header">
          <h3 class="card-title">{{ t('orders.submittedTitle') }} ({{ submittedOrders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th>{{ t('orders.table.orderNumber') }}</th>
                <th>{{ t('orders.table.items') }}</th>
                <th>{{ t('orders.table.orderDate') }}</th>
                <th>{{ t('orders.table.expectedDelivery') }}</th>
                <th>{{ t('orders.table.leadTime') }}</th>
                <th>{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in submittedOrders" :key="order.id">
                <td><strong>{{ order.order_number }}</strong></td>
                <td>{{ t('orders.itemsCount', { count: order.items.length }) }}</td>
                <td>{{ formatDate(order.order_date) }}</td>
                <td>{{ formatDate(order.expected_delivery) }}</td>
                <td>{{ t('restocking.days', { count: submittedLeadTime(order) }) }}</td>
                <td><strong>{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
```

- [ ] **Step 5: Add the `Submitted` status class (cosmetic clarity)**

In `getOrderStatusClass`, add `'Submitted': 'info'` to `statusMap`. Behaviorally a no-op (the function already falls back to `'info'`), but makes intent explicit.

- [ ] **Step 6: Verify end-to-end in the browser**

With both servers running: go to `/restocking`, click Place Order, then open `/orders`. Confirm a Submitted Orders section shows the new `RST-2026-####` order with a lead-time value (10 days for the default $2,000 recommendation), and that it does **not** also appear in All Orders. Change the status filter in the FilterBar to e.g. Delivered — confirm the Submitted Orders section is still visible (proves filter-independence).

- [ ] **Step 7: Commit**

```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab
git add client/src/views/Orders.vue
git commit -m "feat(restocking): show submitted orders section in Orders tab"
```

---

## Task 7: Internationalization strings

**Files:**
- Modify: `client/src/locales/en.js`
- Modify: `client/src/locales/ja.js`

**Interfaces:**
- Consumes: nothing.
- Produces: the `nav.restocking`, `status.submitted`, `restocking.*`, and `orders.submittedTitle`/`orders.table.leadTime` keys referenced by Tasks 5–6.

- [ ] **Step 1: Add English strings**

In `client/src/locales/en.js`: add `restocking: 'Restocking'` to the `nav` object; add `submitted: 'Submitted'` to the `status` object; add `submittedTitle: 'Submitted Orders'` to `orders` and `leadTime: 'Lead Time'` to `orders.table`; and add a new top-level `restocking` block:
```javascript
  restocking: {
    title: 'Restocking',
    description: 'Set a budget and restock the items your forecast needs most.',
    budgetLabel: 'Available budget',
    recommendedTitle: 'Recommended Restock',
    empty: 'No items to restock within this budget.',
    totalCost: 'Total cost',
    remaining: 'Remaining budget',
    placeOrder: 'Place Order',
    placing: 'Placing order...',
    success: 'Order {orderNumber} submitted.',
    viewInOrders: 'View in Orders',
    days: '{count} days',
    table: {
      item: 'Item',
      trend: 'Trend',
      unitCost: 'Unit Cost',
      quantity: 'Quantity',
      lineCost: 'Line Cost',
      leadTime: 'Lead Time'
    }
  },
```

- [ ] **Step 2: Add Japanese strings**

In `client/src/locales/ja.js`: add `restocking: '再入荷'` to `nav`; add `submitted: '送信済み'` to `status`; add `submittedTitle: '送信済み注文'` to `orders` and `leadTime: 'リードタイム'` to `orders.table`; and add:
```javascript
  restocking: {
    title: '再入荷',
    description: '予算を設定し、予測で最も必要な品目を補充します。',
    budgetLabel: '利用可能予算',
    recommendedTitle: '推奨補充',
    empty: 'この予算内で補充する品目はありません。',
    totalCost: '合計費用',
    remaining: '残り予算',
    placeOrder: '注文する',
    placing: '注文中...',
    success: '注文 {orderNumber} を送信しました。',
    viewInOrders: '注文で表示',
    days: '{count}日',
    table: {
      item: '品目',
      trend: '傾向',
      unitCost: '単価',
      quantity: '数量',
      lineCost: '小計',
      leadTime: 'リードタイム'
    }
  },
```

- [ ] **Step 3: Verify both locales render**

Reload `/restocking` and `/orders`; confirm all labels are human-readable (no raw `restocking.*` keys). Toggle the language switcher to Japanese and confirm the Restocking tab, table headers, and Submitted Orders section are translated.

- [ ] **Step 4: Commit**

```bash
cd /Users/jay/anthropic-basecamp/wt-restocking-tab
git add client/src/locales/en.js client/src/locales/ja.js
git commit -m "feat(restocking): add en/ja strings for restocking and submitted orders"
```

---

## Task 8: Full-feature verification

**Files:** none (verification only)

- [ ] **Step 1: Backend suite green**

Run: `cd server && uv run pytest ../tests/backend -q`
Expected: all tests pass (40 baseline + new restocking tests).

- [ ] **Step 2: End-to-end walk-through**

With both servers running, drive the full flow (Playwright MCP if approved, else manually in the browser):
1. `/restocking` → slider at $2,000 shows WDG-001 ×150 + FLT-405 ×20, total $2,000, remaining $0.
2. Drag slider to $5,000 → all 8 positive-gap items shown, total $3,979.48.
3. Drag to $500 → smaller/partial recommendation; drag to $0 → empty state.
4. Back to a non-zero budget → Place Order → success message with `RST-2026-####`.
5. `/orders` → Submitted Orders section shows the order with lead time; it's absent from All Orders.
6. Set the FilterBar status to Delivered → Submitted Orders section remains visible.
7. Toggle language to Japanese → labels translated.

- [ ] **Step 3: Final commit / clean tree**

Run: `cd /Users/jay/anthropic-basecamp/wt-restocking-tab && git status`
Expected: clean working tree (all changes committed across Tasks 1–7).

---

## Self-Review Notes (author)

- **Spec coverage:** budget slider (Task 5), trend-first budget recommendations (Task 2), Place Order submit (Tasks 3–5), Submitted Orders section with lead time (Task 6), filter-independence + `Order.id` + year-from-now + datetime arithmetic (Tasks 3/6), i18n both locales (Task 7), pytest + browser verification (Tasks 1–3, 8). FilterBar intentionally untouched (Global Constraints / Task 6 note).
- **No placeholders:** every code step contains full content; no TBDs.
- **Type consistency:** `recommended_quantity`/`line_cost`/`item_sku` names match across backend models, api.js payloads, and the Vue components; POST body keys (`item_sku, item_name, quantity, unit_cost, lead_time_days`) match `RestockOrderLine`.
