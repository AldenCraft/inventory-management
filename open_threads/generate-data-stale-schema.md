# generate_data.py regenerates orders in a stale schema incompatible with the committed data

**Status:** ✅ Fixed by [#7](https://github.com/AldenCraft/inventory-management/pull/7) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`server/generate_data.py` carries an old product catalog, warehouse list, and category set that no longer match the committed JSON data or the frontend dropdowns. Its warehouses are `["A", "B", "C"]` while `inventory.json`/`orders.json` use `"San Francisco"`/`"London"`/`"Tokyo"`; its categories are Widgets/Components/Equipment/Consumables while the real data uses Circuit Boards/Sensors/Power Supplies/Controllers/Actuators; its SKUs are `WDG-001`/`BRG-102`/… while the real inventory uses `PCB-001`/`PSU-501`/`TMP-201`/etc. Running the script silently overwrites `data/orders.json` with data that joins to nothing.

## Where
- `server/generate_data.py:42` — `warehouses = ["A", "B", "C"]` (real data uses San Francisco/London/Tokyo — confirmed via `server/data/inventory.json`).
- `server/generate_data.py:9-27` — `products` list uses categories Widgets/Components/Equipment/Consumables and SKUs WDG-001/BRG-102/MTR-304/FLT-405/VLV-506/… none of which exist in `inventory.json`.
- `server/generate_data.py:120-121` — `json.dump(orders, ...)` overwrites `data/orders.json` (only orders; it never regenerates inventory/backlog/demand).
- `server/generate_data.py:51` etc. — uses `random.*` with no seed, so output is non-reproducible.

## Repro
`cd server && python generate_data.py` overwrites `data/orders.json` with orders whose `warehouse` (A/B/C), `category` (Widgets/…), and item `sku` (WDG-001/…) match nothing in `inventory.json` or the frontend filter dropdowns. Every warehouse and category filter then returns empty, and any SKU-based join against inventory finds no rows.

## Fix / acceptance criteria
- Bring the generator's `products`, `warehouses`, and `categories` in line with `server/data/inventory.json` (San Francisco/London/Tokyo; Circuit Boards/Sensors/Power Supplies/Controllers/Actuators; real SKUs), or delete `generate_data.py` if the JSON is now hand-maintained.
- Add `random.seed(...)` for reproducible output.
- If kept, have it regenerate inventory/backlog/demand alongside orders (or clearly document that it only touches orders) so the datasets stay referentially consistent.
