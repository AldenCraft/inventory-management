from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def matches_category(item: dict, category: str) -> bool:
    """True if `item` belongs to `category`.

    Inventory items carry a single top-level `category`. Orders can mix
    categories across their line items, so an order matches if its top-level
    category (the display label) OR any of its line items is in `category`.
    Matching the line items is what keeps a multi-category order from being
    dropped by a filter for one of its non-primary categories.
    """
    target = category.lower()
    if item.get('category', '').lower() == target:
        return True
    return any(line.get('category', '').lower() == target for line in item.get('items', []))

def order_revenue_for_category(order: dict, category: Optional[str]) -> float:
    """Revenue from `order` attributable to `category`.

    With no category filter the whole order value counts. With a filter, only
    the line items in that category count, so a mixed-category order splits its
    value across categories instead of assigning it all to the primary one.
    """
    if not category or category == 'all':
        return order.get('total_value', 0)
    target = category.lower()
    return sum(
        line.get('quantity', 0) * line.get('unit_price', 0)
        for line in order.get('items', [])
        if line.get('category', '').lower() == target
    )

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if matches_category(item, category)]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

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


class RestockOrderLine(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    lead_time_days: int


class CreateRestockOrderRequest(BaseModel):
    items: List[RestockOrderLine]

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class Task(BaseModel):
    id: int
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    dueDate: str

# In-memory task store. Starts empty and lives for the life of the process
# (restart clears it), matching the rest of this demo's mock-data approach.
# The client seeds its own example tasks (ids 1-4) in useAuth.js and merges them
# with the tasks returned here, so server-assigned ids start at 1000 to avoid
# colliding with those client-side mock ids — App.vue distinguishes mock tasks
# from API tasks by id when deleting/toggling.
tasks_store: List[dict] = []
_next_task_id = 1000

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

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

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    # Attribute revenue per line item so a category filter counts only the
    # matching lines of each order, not the whole (possibly mixed) order value.
    # Exclude "Submitted" restock orders: they're internal procurement, not
    # customer revenue, so they must not inflate the Overview revenue KPI.
    total_orders_value = sum(
        order_revenue_for_category(order, category)
        for order in filtered_orders
        if order["status"] != "Submitted"
    )

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": round(total_orders_value, 2)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all user-created tasks stored on the server for this session."""
    return tasks_store

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(task: CreateTaskRequest):
    """Create a task and keep it in the in-memory store for this session."""
    global _next_task_id
    new_task = {
        "id": _next_task_id,
        "title": task.title,
        "priority": task.priority,
        "dueDate": task.dueDate,
        "status": "pending",
    }
    _next_task_id += 1
    # Newest first, matching how the client prepends and renders tasks.
    tasks_store.insert(0, new_task)
    return new_task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task by id."""
    global tasks_store
    if not any(t["id"] == task_id for t in tasks_store):
        raise HTTPException(status_code=404, detail="Task not found")
    tasks_store = [t for t in tasks_store if t["id"] != task_id]
    return {"success": True, "id": task_id}

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: int):
    """Toggle a task between pending and completed."""
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
