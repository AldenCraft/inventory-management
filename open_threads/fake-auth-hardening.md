# Fake auth is presented as real (harden and document)

**Status:** 🟢 Fixed by [#24](https://github.com/AldenCraft/inventory-management/pull/24) — open, held for review

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`client/src/composables/useAuth.js` is mocked authentication presented as if it were real: `isAuthenticated` is hardcoded true and never used for route protection, `logout()` is just an `alert()`, and `getInitials()` throws on a missing or space-less name. There is no token/localStorage misuse and no XSS surface (no `v-html`/`innerHTML`/`eval`; localStorage only holds the locale), so this is acceptable security theater for a demo — but it should say so.

## Items
- [ ] `client/src/composables/useAuth.js:92` — `isAuthenticated = ref(true)` is hardcoded and never read for route protection (`main.js` has no navigation guard). Add a comment documenting that auth is mocked.
- [ ] `client/src/composables/useAuth.js:94-98` — `logout()` is just an `alert()`; document it as a stub (or wire real behavior if gating is ever added).
- [ ] `client/src/composables/useAuth.js:100` — `getInitials` throws on a missing/space-less name; guard against empty/space-less input.
- [ ] `client/src/main.js` — if any real gating is ever wanted, add a navigation guard that reads `isAuthenticated`.

## Suggested approach
Add a comment documenting that auth is mocked, guard `getInitials` against empty/space-less names, and only add a navigation guard if real gating is actually needed.
