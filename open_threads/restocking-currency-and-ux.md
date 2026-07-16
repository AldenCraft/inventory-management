# Restocking: ¥ over un-converted USD, plus loading-flicker and duplicate-submit UX

**Status:** ✅ Fixed by [#33](https://github.com/AldenCraft/inventory-management/pull/33) — merged 2026-07-16

Created: 2026-07-16, from a post-merge review of the inventory-management repo (the earlier whole-app review landed as PRs #4–#30). File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem

Two separate issues on the Restocking page.

**1. Currency not converted (¥ over raw USD).** The view prepended a bare `currencySymbol` (`¥`/`$`) to un-×150'd USD values, so in Japanese mode it showed `¥2,000` where the real figure is `$2,000` (≈`¥300,000`). It also hand-rolled its own `currencySymbol` computed instead of going through the shared currency helpers. This is the Restocking slice of a wider currency-conversion problem; the Orders/Inventory slice is tracked in `currency-not-converted-in-modals-and-views.md` (sibling thread), and mirrors the already-fixed Spending case (`spending-currency-symbol-unconverted.md`, PR #8).

**2. Restocking UX.**
- *Loading flicker.* Every debounced slider change set `loading = true`, which flips the page-level `v-if="loading"` and replaces the whole recommendations table with the loading state on each nudge of the budget slider.
- *Duplicate submit.* After a successful place-order the button re-enabled with the recommendations still intact, so a second click posted a duplicate order for the same line items.

## Where (pre-fix line refs)

- `client/src/views/Restocking.vue:10` — budget label: `{{ currencySymbol }}{{ budget.toLocaleString() }}` (raw USD).
- `client/src/views/Restocking.vue:51,53` — unit cost / line cost cells prepend `currencySymbol` to raw USD.
- `client/src/views/Restocking.vue:61,62` — total cost / remaining summary, same.
- `client/src/views/Restocking.vue:92-95` — hand-rolled `currencySymbol` computed instead of the shared currency helpers.
- `client/src/views/Restocking.vue:113,127-131` — `loadRecommendations` sets `loading=true`; the debounced budget `watch` calls it on every change → table flicker.
- `client/src/views/Restocking.vue:65-71,133-152` — the place-order button and `placeOrder`; button stayed enabled with recommendations intact after success.

## Repro

Currency: switch language/currency to Japanese; the $2,000 budget slider showed `¥2,000` (should be ≈`¥300,000`), and unit/line/total costs all showed `¥` over the raw USD magnitude.

Flicker: drag the budget slider; the recommendations table blinks out to "Loading..." on each debounced re-fetch.

Duplicate submit: place an order, then click "Place Order" again → a second identical restock order is created.

## Fix (this thread)

- Route every money value through `formatCurrency(value, currentCurrency.value)` from `utils/currency.js` (whole values), and `formatCurrencyWithDecimals(value, currency, 2)` for the per-unit cost column. Dropped the hand-rolled `currencySymbol` computed and imported the shared util directly (same pattern as Spending/Reports).
- Added a separate `refreshing` flag: the initial mount uses the full-page `loading` state, but debounced slider re-fetches set `refreshing` instead, so the table stays on screen (a small "Loading…" note appears in the card header).
- Added an `orderPlaced` latch: set on a successful submit and included in the button's `:disabled`, so a second click can't post a duplicate; cleared in the budget `watch` since a new budget means a new recommendation set.

## Acceptance criteria

- In Japanese mode, no on-screen figure mixes the ¥ symbol with an un-converted USD magnitude; a $2,000 budget shows ≈¥300,000.
- Dragging the budget slider re-fetches without the recommendations table disappearing.
- After a successful place-order the button is disabled until the budget changes; no duplicate orders.

## Related

- `currency-not-converted-in-modals-and-views.md` — the Orders/Inventory (and modals) slice of the same currency-conversion issue (sibling thread).
- `spending-currency-symbol-unconverted.md` (PR #8) — the already-fixed Spending equivalent.
- The #30 thread (`modal-and-dropdown-accessibility.md`) deferred `useCurrency` adoption in Restocking; this thread supersedes that by moving Restocking straight onto the `formatCurrency` util. The `<td @click>` keyboard-operability sub-item deferred by #30 is also partly addressed here for `Inventory.vue`.
</content>
</invoke>
