# Backlog modal "Expected Date" row always shows N/A (field not in data)

**Status:** ✅ Fixed by [#23](https://github.com/AldenCraft/inventory-management/pull/23) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`BacklogDetailModal` renders an "Expected Date" row bound to `backlogItem.expected_date`, but backlog items have no `expected_date` field. Their keys are `id`, `order_id`, `item_sku`, `item_name`, `quantity_needed`, `quantity_available`, `days_delayed`, `priority`. Because `formatDate` returns `'N/A'` for a falsy value, the row is always "N/A" — a permanently dead field. The modal is opened from the Dashboard, so the empty row is user-visible.

## Where
- `client/src/components/BacklogDetailModal.vue:66` — `<div class="info-value">{{ formatDate(backlogItem.expected_date) }}</div>` under the "Expected Date" label.
- `server/data/backlog_items.json` — item objects contain no `expected_date` key.
- `client/src/views/Dashboard.vue:283-287` — Dashboard mounts `BacklogDetailModal` and opens it via `showBacklogDetail` (line 648), so the row shows to users.

## Repro
On the Dashboard, click a row in "Inventory Shortages" to open the modal. The "Expected Date" field always reads "N/A" regardless of which backlog item is selected.

## Fix / acceptance criteria
- Either remove the "Expected Date" info-item from the modal, or add an `expected_date` field to `backlog_items.json` (and the `BacklogItem` Pydantic model in `server/main.py`) and populate it.
