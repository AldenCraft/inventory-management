# v-for loops keyed by array index instead of a stable identifier

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
Several `v-for` loops key on the array index rather than a stable identifier. This is the repo's #1 listed common issue (client CLAUDE.md: "Use unique keys in v-for (not `index`)"). With index keys, Vue reuses the wrong DOM nodes when the list is reordered or filtered, so rows and chart bars can show stale or mismatched data.

## Where
- `client/src/views/Reports.vue:28` — quarterly table row `v-for="(q, index) in quarterlyData" :key="index"` (should key on `q.quarter`).
- `client/src/views/Reports.vue:51` — monthly bar chart `v-for="(month, index) in monthlyData" :key="index"` (should key on `month.month`).
- `client/src/views/Reports.vue:82` — month-over-month table `v-for="(month, index) in monthlyData" :key="index"` (should key on `month.month`).
- `client/src/views/Orders.vue:57` — nested order line-items loop `v-for="(item, idx) in order.items" :key="idx"`; line items carry a `sku` field, so key on `item.sku`.

## Repro
Apply a filter (or change the time period) that reorders/reduces `monthlyData` or the orders list, then observe rows/bars: with index keys Vue reuses nodes positionally, so a bar's `:title`/height or a row's cells can bind to the wrong record after the list changes.

## Fix / acceptance criteria
- Key each loop on the stable identifier: `q.quarter`, `month.month`, and `item.sku` respectively.
- No `:key="index"` / `:key="idx"` remaining in these loops.
