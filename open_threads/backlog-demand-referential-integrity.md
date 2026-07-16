# Broken referential integrity in backlog and demand data (phantom orders and SKUs)

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`backlog_items.json` and `demand_forecasts.json` reference orders and SKUs that don't exist in the rest of the dataset. All four backlog `order_id`s (ORD-2025-0927..0930) are beyond the real order range — `orders.json` only goes up to ORD-2025-0250 — and their `item_sku`s (FLT-405, MTR-304, VLV-506, WDG-001) aren't in `inventory.json`. In `demand_forecasts.json`, 8 of the 9 `item_sku`s are absent from inventory (only PSU-501 exists). A test even hardcodes two of the phantom SKUs as "expected," cementing the bad data.

## Where
- `server/data/backlog_items.json:4,14,24,34` — `order_id`s ORD-2025-0927/0928/0929/0930; max real order is ORD-2025-0250 (confirmed in `server/data/orders.json`).
- `server/data/backlog_items.json:5,15,25,35` — `item_sku`s FLT-405, MTR-304, VLV-506, WDG-001; none present in `server/data/inventory.json` (inventory uses PCB-/PSU-/TMP-/SRV-/etc.).
- `server/data/demand_forecasts.json` — SKUs WDG-001, BRG-102, GSK-203, MTR-304, FLT-405, VLV-506, SNR-420, CTL-330 are all absent from inventory; only PSU-501 (id 7) exists.
- `tests/backend/test_misc_endpoints.py:77-78` — asserts phantom SKUs `SNR-420` and `CTL-330` are present ("Missing Temperature Sensor Module" / "Missing Logic Controller Board"), locking in the bad data.

## Repro
`GET /api/backlog` returns four rows whose `order_id` and `item_sku` reference nothing else in the system; `GET /api/demand` returns nine rows, eight of which name SKUs not in inventory. Any join from a backlog/demand row back to inventory or orders (e.g. a future restock/purchase-order flow) resolves to nothing.

## Fix / acceptance criteria
- Regenerate `backlog_items.json` and `demand_forecasts.json` using real SKUs from `inventory.json` and real order numbers from `orders.json`.
- Update `tests/backend/test_misc_endpoints.py:77-78` to assert against real SKUs.
- Add a referential-integrity test: every backlog `order_id` exists in orders and every backlog/demand `item_sku` exists in inventory.
