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
