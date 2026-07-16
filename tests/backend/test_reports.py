"""
Tests for the reporting endpoints: /api/reports/quarterly and
/api/reports/monthly-trends.

These two endpoints carry the app's densest arithmetic (per-quarter averages,
the fulfillment-rate division, and the `total_orders > 0` guard), so rather than
smoke-checking that keys exist, each test recomputes the expected aggregate from
/api/orders and compares. That way a future change to the summation, the
division, or the quarter boundaries actually fails a test.
"""
import pytest

# The same quarter boundaries the endpoint uses, kept local so the test breaks
# if the endpoint's month->quarter mapping silently drifts.
QUARTER_OF = {
    "2025-01": "Q1-2025", "2025-02": "Q1-2025", "2025-03": "Q1-2025",
    "2025-04": "Q2-2025", "2025-05": "Q2-2025", "2025-06": "Q2-2025",
    "2025-07": "Q3-2025", "2025-08": "Q3-2025", "2025-09": "Q3-2025",
    "2025-10": "Q4-2025", "2025-11": "Q4-2025", "2025-12": "Q4-2025",
}


def _aggregate_by(orders, key_fn):
    """Roll orders up into {key: {count, revenue, delivered}} using key_fn."""
    agg = {}
    for order in orders:
        key = key_fn(order)
        if key is None:
            continue
        bucket = agg.setdefault(key, {"count": 0, "revenue": 0.0, "delivered": 0})
        bucket["count"] += 1
        bucket["revenue"] += order["total_value"]
        if order["status"] == "Delivered":
            bucket["delivered"] += 1
    return agg


class TestQuarterlyReport:
    """Arithmetic and shape of /api/reports/quarterly."""

    def test_quarterly_response_shape(self, client):
        """Every quarter row carries the full set of computed fields."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for row in data:
            for field in (
                "quarter", "total_orders", "total_revenue",
                "delivered_orders", "avg_order_value", "fulfillment_rate",
            ):
                assert field in row, f"Missing {field} in quarterly row {row}"

        # Rows come back sorted by quarter label.
        quarters = [row["quarter"] for row in data]
        assert quarters == sorted(quarters)

    def test_quarterly_arithmetic_matches_orders(self, client):
        """Totals, averages, and fulfillment rate recompute from the raw orders."""
        orders = client.get("/api/orders").json()
        expected = _aggregate_by(orders, lambda o: QUARTER_OF.get(o["order_date"][:7]))

        data = client.get("/api/reports/quarterly").json()
        by_quarter = {row["quarter"]: row for row in data}

        # Same set of quarters, nothing invented or dropped.
        assert set(by_quarter) == set(expected)

        for quarter, exp in expected.items():
            row = by_quarter[quarter]
            assert row["total_orders"] == exp["count"]
            assert row["delivered_orders"] == exp["delivered"]
            assert abs(row["total_revenue"] - exp["revenue"]) < 0.01

            # avg_order_value = total_revenue / total_orders
            expected_avg = round(exp["revenue"] / exp["count"], 2)
            assert abs(row["avg_order_value"] - expected_avg) < 0.01, \
                f"{quarter}: avg {row['avg_order_value']} != {expected_avg}"

            # fulfillment_rate = delivered / total * 100
            expected_rate = round(exp["delivered"] / exp["count"] * 100, 1)
            assert abs(row["fulfillment_rate"] - expected_rate) < 0.05, \
                f"{quarter}: rate {row['fulfillment_rate']} != {expected_rate}"

    def test_quarterly_total_orders_guard(self, client):
        """Only quarters with orders appear, and each is fully populated.

        avg_order_value and fulfillment_rate are only assigned inside the
        `total_orders > 0` branch, so a returned row that lacks them (or reports
        zero orders) would mean the guard let an empty quarter through.
        """
        data = client.get("/api/reports/quarterly").json()
        for row in data:
            assert row["total_orders"] > 0
            assert row["avg_order_value"] > 0
            assert 0 <= row["fulfillment_rate"] <= 100
            # A real division happened, not the initial 0 placeholder left in place.
            assert row["delivered_orders"] <= row["total_orders"]


class TestMonthlyTrends:
    """Arithmetic and shape of /api/reports/monthly-trends."""

    def test_monthly_trends_shape_and_order(self, client):
        """Rows carry the expected fields and are sorted chronologically."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for row in data:
            for field in ("month", "order_count", "revenue", "delivered_count"):
                assert field in row, f"Missing {field} in monthly row {row}"

        months = [row["month"] for row in data]
        assert months == sorted(months)

    def test_monthly_trends_counts_and_revenue_match_orders(self, client):
        """Per-month counts and revenue recompute from the raw orders."""
        orders = client.get("/api/orders").json()
        expected = _aggregate_by(orders, lambda o: o["order_date"][:7])

        data = client.get("/api/reports/monthly-trends").json()
        by_month = {row["month"]: row for row in data}

        assert set(by_month) == set(expected)

        for month, exp in expected.items():
            row = by_month[month]
            assert row["order_count"] == exp["count"]
            assert row["delivered_count"] == exp["delivered"]
            assert abs(row["revenue"] - exp["revenue"]) < 0.01
            # Delivered can never exceed total orders in the month.
            assert row["delivered_count"] <= row["order_count"]
