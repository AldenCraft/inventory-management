# Backlog view is entirely hardcoded English (no i18n)

**Status:** ✅ Fixed by [#13](https://github.com/AldenCraft/inventory-management/pull/13) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`Backlog.vue` never imports `useI18n`. Every visible string is hardcoded English — the title, description, loading text, stat labels, all table headers, the empty state, the "units short" / "days" suffixes, and the raw lowercase `{{ item.priority }}` value. Switching the app to Japanese leaves this entire page in English. Reusable keys already exist (`status.*`, `priority.*`, `dashboard.backlog.*` in `en.js`/`ja.js`).

## Where
- `client/src/views/Backlog.vue` — no `useI18n` import; `t(` is never used.
- `client/src/views/Backlog.vue:8` — `Loading backlog...`; `:13` `High Priority`; `:25` `Total Backlog Items`.
- `client/src/views/Backlog.vue:43-50` — hardcoded `<th>` headers (Order ID, SKU, Item Name, Quantity Needed, …, Priority).
- `client/src/views/Backlog.vue:62` — `... units short`; `:72` — `{{ item.priority }}` rendered raw/lowercase.

## Repro
1. Switch the app language to Japanese.
2. Navigate to the Backlog page — title, stats, table headers, empty state, and the priority values all remain English.

## Fix / acceptance criteria
- Import `useI18n` and route every string through `t()`, reusing the existing `status.*`, `priority.*`, and `dashboard.backlog.*` keys where they exist.
- Translate the `item.priority` value rather than printing the raw lowercase string.
- The Backlog page is fully localized when the locale is `ja`.
---
