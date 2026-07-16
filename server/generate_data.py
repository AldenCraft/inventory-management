"""
Regenerate server/data/orders.json with sample orders spread across 2025.

Scope: this script ONLY regenerates orders.json. The other datasets
(inventory, demand_forecasts, backlog_items, spending, transactions,
purchase_orders) are hand-maintained and are treated as the source of truth --
in particular, the product catalog below is derived from inventory.json so the
generated orders always reference real SKUs / categories / warehouses and stay
join-compatible with inventory. Previously this catalog was hard-coded and had
drifted (Widgets/Components, warehouses A/B/C, SKUs WDG-*/BRG-*), so running the
script silently overwrote orders.json with data that joined to nothing.

A fixed random seed makes the output reproducible: re-running produces the same
orders.json byte-for-byte.
"""
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Deterministic output so a regeneration is reproducible and reviewable.
random.seed(42)

# Resolve paths relative to this file so the script works regardless of the
# current working directory.
DATA_DIR = Path(__file__).resolve().parent / "data"
INVENTORY_FILE = DATA_DIR / "inventory.json"
ORDERS_FILE = DATA_DIR / "orders.json"

# Match the committed dataset's scale and numbering (ORD-2025-0001 .. 0250) so
# any references into the order-number space (e.g. backlog order_id) keep
# resolving.
TARGET_ORDERS = 250

# Derive the product catalog from the committed inventory. This is the fix for
# the schema drift: real SKUs, names, categories, and warehouses all come from
# the same source the frontend filters and inventory joins use.
with open(INVENTORY_FILE) as f:
    inventory = json.load(f)

products = [
    {
        "sku": item["sku"],
        "name": item["name"],
        "category": item["category"],
        # Use the inventory unit_cost as the order line price so an order line's
        # price is consistent with the item it references.
        "price": item["unit_cost"],
    }
    for item in inventory
]

# Warehouses come straight from inventory (San Francisco / London / Tokyo).
warehouses = sorted({item["warehouse"] for item in inventory})

customers = [
    "Acme Manufacturing Corp", "TechBuild Industries", "Global Parts Ltd",
    "Precision Tools Inc", "Industrial Solutions Inc", "MegaCorp Industries",
    "BuildTech Co", "FastAssembly Ltd", "Quality Parts LLC", "Superior Manufacturing",
    "PrecisionWorks Inc", "Elite Systems Corp", "Advanced Components Inc",
    "ProManufacturing LLC", "TechSolutions Group", "Innovative Parts Co",
    "Premier Industries", "Dynamic Systems Ltd", "Quantum Manufacturing",
    "Apex Engineering", "Titan Products Inc", "Vanguard Systems",
    "Omega Manufacturing", "Fusion Industries", "Stellar Components Ltd",
    "Nexus Engineering", "Cascade Manufacturing", "Horizon Technologies",
    "Summit Parts Corp", "Velocity Industries"
]

statuses = ["Delivered", "Shipped", "Processing", "Backordered"]

# Spread TARGET_ORDERS across the 12 months as evenly as possible, then scatter
# the remainder into a few random months so counts vary month to month while the
# total stays exactly TARGET_ORDERS.
orders_per_month = [TARGET_ORDERS // 12] * 12
for month_index in random.sample(range(12), TARGET_ORDERS % 12):
    orders_per_month[month_index] += 1

orders = []
order_id = 1

for month in range(1, 13):  # Jan to Dec
    for _ in range(orders_per_month[month - 1]):
        # Random day in the month
        day = random.randint(1, 28)  # Using 28 to avoid month-end issues
        hour = random.randint(8, 17)
        minute = random.randint(0, 59)

        order_date = f"2025-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"

        # Expected delivery 7-14 days later
        order_datetime = datetime(2025, month, day, hour, minute)
        delivery_days = random.randint(7, 14)
        expected_delivery = order_datetime + timedelta(days=delivery_days)

        # Determine status based on date (earlier orders more likely to be delivered)
        if month <= 8:
            status = random.choices(statuses, weights=[70, 20, 5, 5])[0]
        elif month <= 10:
            status = random.choices(statuses, weights=[40, 40, 15, 5])[0]
        else:
            status = random.choices(statuses, weights=[10, 30, 40, 20])[0]

        # Select 1-3 products for the order
        num_items = random.randint(1, 3)
        order_products = random.sample(products, num_items)

        items = []
        total_value = 0
        primary_category = None

        for product in order_products:
            quantity = random.randint(50, 1000)
            item_value = quantity * product["price"]
            total_value += item_value

            if primary_category is None:
                primary_category = product["category"]

            items.append({
                "sku": product["sku"],
                "name": product["name"],
                # Carry each line item's own category so revenue and category
                # filtering can be attributed per line item. Without this, a
                # mixed-category order could only be tagged with a single
                # category (see order["category"] below), which both
                # over-counted the primary category and dropped the order from
                # filters for its other categories.
                "category": product["category"],
                "quantity": quantity,
                "unit_price": product["price"]
            })

        warehouse = random.choice(warehouses)

        order = {
            "id": str(order_id),
            "order_number": f"ORD-2025-{order_id:04d}",
            "customer": random.choice(customers),
            "items": items,
            "status": status,
            "warehouse": warehouse,
            # Display-only label (the first line item's category). Revenue
            # attribution and category filtering use the per-line-item
            # categories in "items" above, not this field, so mixed-category
            # orders are counted correctly.
            "category": primary_category,
            "order_date": order_date,
            "expected_delivery": expected_delivery.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_value": round(total_value, 2)
        }

        if status == "Delivered" and month <= 10:
            actual_delivery = order_datetime + timedelta(days=random.randint(6, delivery_days + 2))
            order["actual_delivery"] = actual_delivery.strftime("%Y-%m-%dT%H:%M:%S")

        orders.append(order)
        order_id += 1

# Save to file
with open(ORDERS_FILE, 'w') as f:
    json.dump(orders, f, indent=2)

print(f"Generated {len(orders)} orders across 12 months of 2025")

# Count orders per month
month_counts = defaultdict(int)
for order in orders:
    month = order['order_date'][5:7]
    month_counts[month] += 1

print("\nOrders per month:")
for month in sorted(month_counts.keys()):
    print(f"  {month}: {month_counts[month]} orders")
