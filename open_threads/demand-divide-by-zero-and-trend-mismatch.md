# Demand view: divide-by-zero on change %, and trend badge can disagree with change color

**Status:** ✅ Fixed by [#20](https://github.com/AldenCraft/inventory-management/pull/20) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
Two issues in the Demand view. (1) `getChangePercent` and `getChangeColor` both divide by `forecast.current_demand` with no guard; if it is 0 the result is `Infinity`/`NaN` (latent — no current forecast has `current_demand === 0`). (2) The trend badge renders the raw `forecast.trend` value from the data, while the change-percent color is classified independently by `getChangeColor` (which treats within ±2% as "stable"/blue). The two can disagree: a row whose data says `trend: "increasing"` but whose computed change is ≤2% shows the "increasing" badge next to the blue/stable color.

## Where
- `client/src/views/Demand.vue:173-176` — `getChangePercent`: `(forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand * 100`, no zero guard.
- `client/src/views/Demand.vue:178-190` — `getChangeColor`: divides by `forecast.current_demand` (line 180) and classifies ±2% as stable (line 183), independent of `forecast.trend`.
- `client/src/views/Demand.vue:99-101` — badge uses raw `forecast.trend` (`:class="['badge', forecast.trend]"`, `t(\`trends.${forecast.trend}\`)`).

## Repro
- Divide-by-zero: a forecast with `current_demand: 0` makes `getChangePercent` return `Infinity%` and `getChangeColor` compute `NaN`.
- Trend mismatch: a forecast tagged `trend: "increasing"` with forecasted vs current within ±2% renders the "increasing" badge but the neutral/blue change color.

## Fix / acceptance criteria
- Guard the division (return 0 / `N/A` when `current_demand` is 0).
- Derive the badge and the color from the same source so they cannot disagree (either classify both from the computed change, or drive both from `forecast.trend`).
