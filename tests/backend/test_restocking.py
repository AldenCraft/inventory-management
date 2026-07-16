"""
Tests for restocking API endpoints.
"""
import pytest

import main


class TestRestockingEndpoints:
    """Test suite for restocking recommendations and order submission."""

    @pytest.fixture(autouse=True)
    def restore_global_state(self):
        """Snapshot and restore the module-global mutable state around each test.

        Submitting a restock order appends to the process-global `main.orders`
        list (and bumps `_next_restock_seq`); without teardown those rows leak
        into every later test, so the suite only passed because it happened to
        run in alphabetical order. Restoring here makes each test independent of
        run order. tasks_store / _next_task_id are reset too so this fixture is a
        general isolation guard, not just an orders one.
        """
        orders_snapshot = list(main.orders)
        tasks_snapshot = list(main.tasks_store)
        task_id = main._next_task_id
        restock_seq = main._next_restock_seq
        yield
        main.orders[:] = orders_snapshot          # in-place: same list object endpoints read
        main.tasks_store = tasks_snapshot
        main._next_task_id = task_id
        main._next_restock_seq = restock_seq

    def test_demand_includes_cost_and_lead_time(self, client):
        """Demand forecast items expose unit_cost and lead_time_days."""
        response = client.get("/api/demand")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        for item in data:
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["lead_time_days"], int)
        prs = next(i for i in data if i["item_sku"] == "PRS-203")
        assert prs["unit_cost"] == 12.5
        assert prs["lead_time_days"] == 10

    def test_recommendations_zero_budget_is_empty(self, client):
        response = client.get("/api/restocking/recommendations", params={"budget": 0})
        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"] == []
        assert data["total_cost"] == 0

    def test_recommendations_partial_fill_at_2000(self, client):
        """Budget 2000 -> PRS-203 x150 full, PRX-204 x20 partial, spends exactly 2000."""
        response = client.get("/api/restocking/recommendations", params={"budget": 2000})
        data = response.json()
        recs = data["recommendations"]
        assert [r["item_sku"] for r in recs] == ["PRS-203", "PRX-204"]
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
        assert "SRV-301" not in [r["item_sku"] for r in recs]
        assert data["total_cost"] == pytest.approx(3979.48)
        # increasing-trend items rank ahead of stable ones
        assert recs[0]["item_sku"] == "PRS-203"
        assert [r["trend"] for r in recs[:3]] == ["increasing", "increasing", "increasing"]

    def test_submit_restocking_order(self, client):
        from datetime import datetime
        payload = {"items": [
            {"item_sku": "PRS-203", "item_name": "Pressure Sensor Module",
             "quantity": 150, "unit_cost": 12.5, "lead_time_days": 10},
            {"item_sku": "PRX-204", "item_name": "Proximity Sensor",
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

    def test_dashboard_kpi_excludes_submitted_restock_order(self, client):
        """Restock orders are internal procurement, not customer revenue - the
        Overview total_orders_value KPI must not move when one is submitted."""
        before = client.get("/api/dashboard/summary").json()

        payload = {"items": [
            {"item_sku": "PRS-203", "item_name": "Pressure Sensor Module",
             "quantity": 150, "unit_cost": 12.5, "lead_time_days": 10},
        ]}
        submit_response = client.post("/api/restocking/orders", json=payload)
        assert submit_response.status_code == 200
        order = submit_response.json()

        after = client.get("/api/dashboard/summary").json()
        assert after["total_orders_value"] == before["total_orders_value"]

        # ... but the submitted order does show up in the orders list.
        submitted = client.get("/api/orders", params={"status": "Submitted"}).json()
        assert any(o["id"] == order["id"] for o in submitted)

    def test_filter_after_submit_does_not_crash(self, client):
        """Regression: a submitted restock order carries no warehouse/category,
        so filtering by them used to hit None.lower() and 500. Every filtered
        read must stay 200 after a restock is submitted."""
        payload = {"items": [
            {"item_sku": "PRS-203", "item_name": "Pressure Sensor Module",
             "quantity": 150, "unit_cost": 12.5, "lead_time_days": 10},
        ]}
        submit = client.post("/api/restocking/orders", json=payload)
        assert submit.status_code == 200
        restock_id = submit.json()["id"]

        # Each of these previously 500'd on the restock row.
        for url in (
            "/api/orders?warehouse=Tokyo",
            "/api/orders?category=Sensors",
            "/api/orders?status=Delivered",
            "/api/dashboard/summary?warehouse=Tokyo",
            "/api/dashboard/summary?category=Sensors",
        ):
            resp = client.get(url)
            assert resp.status_code == 200, f"{url} returned {resp.status_code}"

        # The restock order has no warehouse, so a warehouse filter excludes it.
        tokyo = client.get("/api/orders?warehouse=Tokyo").json()
        assert all(o["id"] != restock_id for o in tokyo)

        # And it's still reachable when no filter drops it.
        all_orders = client.get("/api/orders").json()
        assert any(o["id"] == restock_id for o in all_orders)

    def test_monthly_trends_excludes_submitted_restock(self, client):
        """Restock orders are procurement, not revenue: submitting one must not
        change monthly-trends revenue or add a bucket for the restock's month."""
        before = client.get("/api/reports/monthly-trends").json()
        before_revenue = sum(row["revenue"] for row in before)
        before_months = {row["month"] for row in before}

        payload = {"items": [
            {"item_sku": "PRS-203", "item_name": "Pressure Sensor Module",
             "quantity": 150, "unit_cost": 12.5, "lead_time_days": 10},
        ]}
        assert client.post("/api/restocking/orders", json=payload).status_code == 200

        after = client.get("/api/reports/monthly-trends").json()
        after_revenue = sum(row["revenue"] for row in after)
        after_months = {row["month"] for row in after}

        assert after_revenue == pytest.approx(before_revenue)
        # No new month bucket appears for the just-submitted restock order.
        assert after_months == before_months
