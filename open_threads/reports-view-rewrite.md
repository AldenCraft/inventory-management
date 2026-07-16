# Rewrite Reports.vue to match the rest of the app

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`client/src/views/Reports.vue` is the weakest file in the client and reads like it predates the rest of the app: it uses the Options API and calls axios directly in a Composition-API + `api.js` codebase, has zero i18n, is full of debug logging, hand-rolls utilities that already exist, and ignores the global filter bar every other view respects.

## Items
- [ ] `client/src/views/Reports.vue:130,156,162` — Options API + direct axios with hardcoded `http://localhost:8001/api/reports/quarterly` and `.../monthly-trends`; route these through `client/src/api.js` instead.
- [ ] `client/src/views/Reports.vue` — no `useI18n` import; English strings and `$` are hardcoded throughout. Add i18n and use the currency helper.
- [ ] `client/src/views/Reports.vue:145,150,155,158,161,164,167,169,172,176,215,243,256` — remove the `console.log` debug spam; `formatNumber` (line 215) and `getBarHeight` (line 256) log on every cell/bar render.
- [ ] `client/src/views/Reports.vue:214-240` — hand-rolled `formatNumber` duplicates `toLocaleString`/`currency.js`; use the shared helpers.
- [ ] `client/src/views/Reports.vue:255-271` — `getBarHeight` recomputes `maxRevenue` by looping all months on every bar (O(n^2)); make the max a `computed`.
- [ ] `client/src/views/Reports.vue` — the view ignores the global filter bar entirely (inconsistent with Dashboard/Spending); wire it in.

## Suggested approach
Rewrite in the Composition API using `api.js`, `useI18n`, and `currency.js`, memoize the max as a computed, and connect the filter bar. Per the repo `CLAUDE.md`, delegate the significant `.vue` change to the `vue-expert` subagent when this is picked up.
