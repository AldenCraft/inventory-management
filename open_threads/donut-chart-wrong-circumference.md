# Dashboard donut segments scaled to the wrong circumference (~8% too large)

**Status:** ✅ Fixed by [#4](https://github.com/AldenCraft/inventory-management/pull/4) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The Order Health donut uses circles of `r="65"`, whose true circumference is `2·π·65 ≈ 408.4`. The `stroke-dasharray` gap is correctly hardcoded to `408`, but `getCircleSegment` computes the filled arc length against `440`. So each arc is ~7.8% longer than it should be, the cumulative dashoffsets (built from those same segment values) drift, segments overlap and no longer match the true status proportions. With all orders in a single status, the arc wraps past 360°.

## Where
- `client/src/views/Dashboard.vue:88-103` — the four status circles use `r="65"` and `stroke-dasharray="... 408"`; offsets on lines 94, 98, 102 are sums of `getCircleSegment(...)` outputs.
- `client/src/views/Dashboard.vue:594-596` — `getCircleSegment` returns `(value / totalOrders.value) * 440` (mismatched against the 408 gap and the r=65 geometry).

## Repro
On the dashboard, the donut arcs sum to more than the ring and creep over each other. Filter/craft a state where all orders share one status: that status's arc is scaled to 440 against a 408 ring, so it visibly overshoots and wraps past the full circle instead of closing at 360°.

## Fix / acceptance criteria
- Define a single shared `CIRCUMFERENCE = 2 * Math.PI * 65` (≈408.4) and use it for both the segment length in `getCircleSegment` and the `stroke-dasharray` gap, so the two can't drift.
- After the fix, segments sum to exactly the ring and a single-status dataset produces a full, non-overlapping circle.
