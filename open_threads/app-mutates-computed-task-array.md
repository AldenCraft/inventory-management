# App.vue mutates a computed task array that resets on locale switch

**Status:** ✅ Fixed by [#14](https://github.com/AldenCraft/inventory-management/pull/14) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
`useAuth.js` returns `currentUser` as a `computed` keyed on `currentLocale`, and the `tasks` array is built inline from a locale literal each time the computed re-evaluates. `App.vue` mutates that computed directly — splicing tasks out on delete and flipping `status` on toggle. The mutations appear to work, but the moment the locale changes the computed rebuilds from the literal and every task deletion/toggle silently reverts. This violates the "never mutate a computed" rule in `client/CLAUDE.md`.

## Where
- `client/src/composables/useAuth.js:14-89` — `createCurrentUser()` returns `computed(() => ({ ...baseUserData, tasks: isJapanese ? [...] : [...] }))`; `tasks` is a fresh literal on every recompute.
- `client/src/App.vue:116` — `currentUser.value.tasks.splice(index, 1)` mutates the computed's array.
- `client/src/App.vue:135` — `mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'` mutates an object inside the computed.

## Repro
1. Delete or toggle one of the mock tasks in the UI — the change shows.
2. Switch the language (e.g. English → Japanese).
3. The computed rebuilds from the literal and the deleted task reappears / the toggled status resets.

## Fix / acceptance criteria
- Hold the mock tasks in a `ref` (initialized once), and let the `computed` supply only localized labels/derived fields.
- Deletions and status toggles persist across a locale switch.
- No component mutates the `currentUser` computed or its nested arrays/objects.
---
