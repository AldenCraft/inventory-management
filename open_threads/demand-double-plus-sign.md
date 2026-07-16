# Demand view: "Increasing Demand" cards show a double plus ("++50.0%"), and count reads "1 items"

**Status:** 🔨 in progress (local branch, no PR yet)

Created: 2026-07-16, from a post-merge review of the inventory-management repo. File:line references are from the current `main` checkout and may drift — re-locate before acting.

---

## The problem
Two small display issues in the Demand view.

1. **Double plus sign.** `getChangePercent` already returns a signed string for positive
   values (e.g. `+50.0`). The increasing-demand trend card prepended *another* `+` in the
   template, so those rows rendered `++50.0%`. The forecasts table and the stable/decreasing
   cards render correctly (single sign) because they rely on `getChangePercent`'s sign alone.

2. **Pluralization.** The trend-card count uses the shared `demand.itemsCount` locale
   string, which is always plural ("{count} items"). A card with a single item read
   "1 items".

## Where
- `client/src/views/Demand.vue` — increasing card change span: `+{{ getChangePercent(item) }}%`
  (the extra `+` before the interpolation was the bug).
- `client/src/views/Demand.vue` — all three trend-card counts:
  `t('demand.itemsCount', { count: ... })` with no singular form.
- `client/src/locales/en.js:126,191` — `itemsCount: '{count} items'` (plural only).
- `client/src/locales/ja.js:126,191` — `itemsCount: '{count}件'` (counter 件, no plural distinction).

## Fix (applied)
- Removed the extra `+` from the increasing card so every site derives the sign from
  `getChangePercent` alone — one sign everywhere. `N/A` (the zero `current_demand` guard)
  now renders as `N/A%` on the increasing card, consistent with the other cards and the
  table (no more `+N/A%`).
- Added an `itemsCountLabel(count)` helper used by all three cards. It keeps using the
  locale string, but for English drops the trailing "s" when `count === 1` ("1 item").
  Japanese is left untouched (件 has no singular/plural form). This avoids editing the
  locale files, which were out of scope.

## Note / follow-up
The English singular/plural correction lives inline in the view because the shared
`itemsCount` locale key has no singular form. The cleaner long-term fix is a proper
pluralized locale entry (e.g. separate `item`/`items` keys or an ICU-style plural rule)
so the view doesn't string-munge locale output — deferred to keep this change scoped to
`Demand.vue`.
