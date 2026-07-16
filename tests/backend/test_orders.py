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


def _order_matches_category(order, category):
    """Mirror the server's order/category match: top-level label OR any line item."""
    target = category.lower()
    if order.get("category", "").lower() == target:
        return True
    return any(line.get("category", "").lower() == target for line in order["items"])


class TestOrdersFilterReducesResults:
    """Filters must actually shrink the result set, not just leave a key in place.

    A filter that returns the full list (the classic "invalid filter reads as no
    filter" bug) would pass a key-exists check but fail these. Each test asserts
    the filtered count is strictly smaller than unfiltered AND every returned row
    matches the filter.
    """

    def test_month_filter_reduces_and_all_match(self, client):
        """?month=2025-01 returns fewer orders than unfiltered, all in that month."""
        all_orders = client.get("/api/orders").json()
        filtered = client.get("/api/orders?month=2025-01").json()

        assert len(filtered) > 0
        assert len(filtered) < len(all_orders)
        for order in filtered:
            assert "2025-01" in order["order_date"]

    def test_warehouse_filter_reduces_and_all_match(self, client):
        """A warehouse filter shrinks the set and every row is that warehouse."""
        all_orders = client.get("/api/orders").json()
        filtered = client.get("/api/orders?warehouse=Tokyo").json()

        assert len(filtered) > 0
        assert len(filtered) < len(all_orders)
        for order in filtered:
            assert order["warehouse"] == "Tokyo"

    def test_category_filter_reduces_and_all_match(self, client):
        """A category filter shrinks the set and every row carries that category."""
        all_orders = client.get("/api/orders").json()
        filtered = client.get("/api/orders?category=Sensors").json()

        assert len(filtered) > 0
        assert len(filtered) < len(all_orders)
        for order in filtered:
            assert _order_matches_category(order, "Sensors"), \
                f"Order {order['id']} returned by category=Sensors has no Sensors line"

    def test_status_filter_reduces_and_all_match(self, client):
        """A status filter shrinks the set and every row has that status."""
        all_orders = client.get("/api/orders").json()
        filtered = client.get("/api/orders?status=Delivered").json()

        assert len(filtered) > 0
        assert len(filtered) < len(all_orders)
        for order in filtered:
            assert order["status"].lower() == "delivered"


class TestOrdersById:
    """Single-order retrieval and its 404 path."""

    def test_get_order_by_id(self, client):
        """A known order id round-trips through /api/orders/{id}."""
        all_orders = client.get("/api/orders").json()
        assert len(all_orders) > 0
        order_id = all_orders[0]["id"]

        response = client.get(f"/api/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["id"] == order_id

    def test_get_nonexistent_order_returns_404(self, client):
        """An unknown order id returns 404 with a 'not found' detail."""
        response = client.get("/api/orders/nonexistent-order-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
