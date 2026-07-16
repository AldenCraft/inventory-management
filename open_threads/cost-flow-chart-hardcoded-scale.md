# Monthly cost-flow chart uses a hardcoded 25K scale and axis

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`getBarHeight` divides each stacked segment by a fixed `maxValue = 25000`, and the Y-axis labels are hardcoded `25K…0`. The monthly totals (procurement + operational + labor + overhead) are well over 25,000, so bars routinely compute heights over 100% and clip past the plot area, and the axis is meaningless. In JPY the axis is doubly wrong because the labels aren't converted.

## Where
- `client/src/views/Spending.vue:386-389` — `getBarHeight(value)` uses `const maxValue = 25000; return (value / maxValue) * 100`.
- `client/src/views/Spending.vue:83-88` — hardcoded Y-axis `<span>` labels `{{ currencySymbol }}25K` … `{{ currencySymbol }}0`.

## Repro
- A month whose combined spending totals ~$30K produces `getBarHeight(30000)` = 120%, rendering a segment that overflows the chart area.
- With `currencySymbol` = `¥`, the axis reads "¥25K…¥0" without any conversion, so the numbers don't match the JPY bar values.

## Fix / acceptance criteria
- Compute the chart max from the data (as `maxRevenueValue` already does for the revenue chart) instead of a literal 25000.
- Render the Y-axis tick labels from that computed max.
- Convert axis labels for the active currency so they match the bar values.
---
