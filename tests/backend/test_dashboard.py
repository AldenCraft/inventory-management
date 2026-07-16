"""
Tests for dashboard API endpoints.
"""
import pytest


class TestDashboardEndpoints:
    """Test suite for dashboard-related endpoints."""

    def test_get_dashboard_summary(self, client):
        """Test getting dashboard summary."""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

        # Check required fields
        required_fields = [
            "total_inventory_value",
            "low_stock_items",
            "pending_orders",
            "total_backlog_items",
            "total_orders_value"
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_dashboard_summary_data_types(self, client):
        """Test that dashboard summary has correct data types."""
        response = client.get("/api/dashboard/summary")
        data = response.json()

        assert isinstance(data["total_inventory_value"], (int, float))
        assert isinstance(data["low_stock_items"], int)
        assert isinstance(data["pending_orders"], int)
        assert isinstance(data["total_backlog_items"], int)
        assert isinstance(data["total_orders_value"], (int, float))

    def test_dashboard_summary_money_fields_rounded(self, client):
        """Both money fields are rounded to 2 decimals for consistent formatting.

        Regression test: total_orders_value used to be a raw float sum that could
        carry a long fractional tail (e.g. ...0000004) while total_inventory_value
        was rounded. Both should now be round(..., 2).
        """
        # Include a filtered variant so per-line-item revenue summation (which is
        # more prone to float tails) is also exercised.
        for url in ("/api/dashboard/summary", "/api/dashboard/summary?category=Sensors"):
            data = client.get(url).json()
            for field in ("total_inventory_value", "total_orders_value"):
                value = data[field]
                assert round(value, 2) == value, f"{field} not rounded in {url}: {value}"

    def test_dashboard_summary_non_negative_values(self, client):
        """Test that dashboard summary values are non-negative."""
        response = client.get("/api/dashboard/summary")
        data = response.json()

        assert data["total_inventory_value"] >= 0
        assert data["low_stock_items"] >= 0
        assert data["pending_orders"] >= 0
        assert data["total_backlog_items"] >= 0
        assert data["total_orders_value"] >= 0

    def test_dashboard_summary_with_warehouse_filter(self, client):
        """Test dashboard summary with warehouse filter."""
        response = client.get("/api/dashboard/summary?warehouse=San Francisco")
        assert response.status_code == 200

        data = response.json()
        assert "total_inventory_value" in data
        assert "total_orders_value" in data

    def test_dashboard_summary_with_category_filter(self, client):
        """Test dashboard summary with category filter."""
        response = client.get("/api/dashboard/summary?category=Sensors")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_dashboard_summary_with_status_filter(self, client):
        """Test dashboard summary with status filter."""
        response = client.get("/api/dashboard/summary?status=Processing")
        assert response.status_code == 200

        data = response.json()
        # Pending orders should reflect the filter
        assert "pending_orders" in data

    def test_dashboard_summary_with_month_filter(self, client):
        """Test dashboard summary with month filter."""
        response = client.get("/api/dashboard/summary?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_dashboard_summary_with_multiple_filters(self, client):
        """Test dashboard summary with multiple filters."""
        response = client.get(
            "/api/dashboard/summary?warehouse=London&category=Sensors&status=Delivered&month=2025-01"
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        # All required fields should still be present
        assert "total_inventory_value" in data
        assert "total_orders_value" in data

    def test_dashboard_summary_with_all_filters(self, client):
        """Test that 'all' filter values work correctly."""
        response = client.get(
            "/api/dashboard/summary?warehouse=all&category=all&status=all&month=all"
        )
        assert response.status_code == 200

        # Should return same as no filters
        response_no_filter = client.get("/api/dashboard/summary")
        assert response.json() == response_no_filter.json()

    def test_dashboard_summary_power_supplies_filter(self, client):
        """Test dashboard summary with Power Supplies category filter."""
        response = client.get("/api/dashboard/summary?category=Power Supplies")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        # Should have inventory value for Power Supplies items
        assert data["total_inventory_value"] >= 0

    def test_dashboard_pending_orders_calculation(self, client):
        """Test that pending orders are calculated correctly."""
        # Get all orders
        orders_response = client.get("/api/orders")
        all_orders = orders_response.json()

        # Count processing and backordered orders
        pending_count = sum(
            1 for order in all_orders
            if order["status"].lower() in ["processing", "backordered"]
        )

        # Get dashboard summary
        dashboard_response = client.get("/api/dashboard/summary")
        dashboard_data = dashboard_response.json()

        assert dashboard_data["pending_orders"] == pending_count

    def test_dashboard_low_stock_items_calculation(self, client):
        """Test that low stock items are calculated correctly."""
        # Get all inventory
        inventory_response = client.get("/api/inventory")
        all_inventory = inventory_response.json()

        # Count items at or below reorder point
        low_stock_count = sum(
            1 for item in all_inventory
            if item["quantity_on_hand"] <= item["reorder_point"]
        )

        # Get dashboard summary
        dashboard_response = client.get("/api/dashboard/summary")
        dashboard_data = dashboard_response.json()

        assert dashboard_data["low_stock_items"] == low_stock_count

    def test_dashboard_inventory_value_calculation(self, client):
        """Test that total inventory value is calculated correctly."""
        # Get all inventory
        inventory_response = client.get("/api/inventory")
        all_inventory = inventory_response.json()

        # Calculate total value
        expected_value = sum(
            item["quantity_on_hand"] * item["unit_cost"]
            for item in all_inventory
        )

        # Get dashboard summary
        dashboard_response = client.get("/api/dashboard/summary")
        dashboard_data = dashboard_response.json()

        # Allow small floating point differences
        assert abs(dashboard_data["total_inventory_value"] - expected_value) < 0.01


class TestCategoryRevenueAttribution:
    """Revenue must be attributed per line item, not entirely to an order's primary category.

    Guards the misattribution where a mixed-category order counted 100% of its
    value under its first item's category and was dropped from filters for its
    other categories.
    """

    def test_category_revenue_is_per_line_item(self, client):
        """Filtered revenue for a category equals the sum of only that category's line items."""
        orders = client.get("/api/orders").json()
        categories = sorted({
            line["category"] for order in orders for line in order["items"]
        })
        assert categories, "No line-item categories found"

        for category in categories:
            expected = round(sum(
                line["quantity"] * line["unit_price"]
                for order in orders
                for line in order["items"]
                if line["category"].lower() == category.lower()
            ), 2)
            data = client.get(f"/api/dashboard/summary?category={category}").json()
            assert abs(data["total_orders_value"] - expected) < 0.01, \
                f"{category}: dashboard {data['total_orders_value']} != per-line-item {expected}"

    def test_category_revenues_partition_total(self, client):
        """Per-category revenues should sum to the full line-item revenue.

        Each order's value is split across its line categories, so nothing is
        double-counted (over-count) or lost (under-count).
        """
        orders = client.get("/api/orders").json()
        categories = sorted({line["category"] for o in orders for line in o["items"]})

        per_category_total = sum(
            client.get(f"/api/dashboard/summary?category={c}").json()["total_orders_value"]
            for c in categories
        )
        raw_line_total = sum(
            line["quantity"] * line["unit_price"]
            for o in orders for line in o["items"]
        )
        # Tolerance covers per-category rounding to cents.
        assert abs(per_category_total - raw_line_total) < len(categories) * 0.01 + 0.01

    def test_multi_category_order_not_dropped_by_filter(self, client):
        """A mixed-category order must appear when filtering by any of its categories."""
        orders = client.get("/api/orders").json()
        mixed = next(
            (o for o in orders if len({line["category"] for line in o["items"]}) >= 2),
            None,
        )
        assert mixed is not None, "Expected at least one multi-category order in sample data"

        primary = mixed["items"][0]["category"]
        non_primary = next(
            line["category"] for line in mixed["items"] if line["category"] != primary
        )
        filtered = client.get(f"/api/orders?category={non_primary}").json()
        assert any(o["id"] == mixed["id"] for o in filtered), \
            "Multi-category order dropped when filtering by a non-primary category"
