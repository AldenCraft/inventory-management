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
