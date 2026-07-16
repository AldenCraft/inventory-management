# Inventory detail modal shows the bin under "Warehouse", never the city

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
An inventory item has two distinct fields: `warehouse` (the city — San Francisco / London / Tokyo) and `location` (the bin, e.g. "Warehouse A-12"). The detail modal's "Warehouse" info-item passes `inventoryItem.location` into `translateWarehouse(...)`, so it renders the bin instead of the city — duplicating the "Location" row two items up — and the actual warehouse city is never shown anywhere in the modal.

## Where
- `client/src/components/InventoryDetailModal.vue:84` — `{{ translateWarehouse(inventoryItem.location) }}` inside the "Warehouse" info-item.
- `client/src/components/InventoryDetailModal.vue:53` — the "Location" row already shows `{{ inventoryItem.location }}` (the same bin value).

## Repro
1. Open the detail modal for any inventory item.
2. "Location" shows e.g. "Warehouse A-12" and "Warehouse" shows the same "Warehouse A-12" (translated) — the item's city (`warehouse`) appears nowhere.

## Fix / acceptance criteria
- The "Warehouse" info-item passes `inventoryItem.warehouse` to `translateWarehouse(...)`.
- The modal shows the city (San Francisco / London / Tokyo) under "Warehouse" and the bin under "Location", with no duplication.
---
