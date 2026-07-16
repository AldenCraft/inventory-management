"""
Tests for orders API endpoints, focused on the month/quarter filter.
"""
import pytest


class TestOrdersMonthFilter:
    """Test suite for the /api/orders month/quarter filter."""

    def test_unknown_quarter_returns_empty(self, client):
        """An unrecognized quarter must not fall through to the full list.

        Regression test: `Q1-2024` (and any quarter not in QUARTER_MAP) used to
        return every order, silently treating an invalid filter as "no filter".
        It should now return an empty list.
        """
        all_orders = client.get("/api/orders").json()
        assert len(all_orders) > 0  # sanity: there is data to (not) return

        response = client.get("/api/orders?month=Q1-2024")
        assert response.status_code == 200

        data = response.json()
        assert data == []
        # Explicitly guard against the old "returns everything" behavior.
        assert len(data) != len(all_orders)

    def test_unknown_quarter_q5_returns_empty(self, client):
        """A quarter-shaped value outside Q1-Q4 also returns empty, not all."""
        response = client.get("/api/orders?month=Q5-2025")
        assert response.status_code == 200
        assert response.json() == []

    def test_known_quarter_filters_correctly(self, client):
        """A recognized quarter still returns only that quarter's orders."""
        response = client.get("/api/orders?month=Q1-2025")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        q1_months = ("2025-01", "2025-02", "2025-03")
        for order in data:
            assert any(m in order["order_date"] for m in q1_months)

    def test_direct_month_filter_still_works(self, client):
        """A direct YYYY-MM month filter is unaffected by the quarter fix."""
        response = client.get("/api/orders?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert "2025-01" in order["order_date"]
