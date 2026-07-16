# Modals and dropdowns have no keyboard/focus accessibility

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
No modal in the app supports escape-to-close, focus trapping, focus return, `role="dialog"`/`aria-modal`, body-scroll-lock, or aria-labels on icon-only close buttons — a grep of `client/src/` finds no `keydown`/`Escape`/focus-management/`role="dialog"` anywhere. Every modal is dismissable only by mouse, which locks out keyboard and screen-reader users. The two dropdowns close via a racy `@blur` + `setTimeout(...,200)` and expose no ARIA state, and the Dashboard donut SVG and clickable table rows are not operable by keyboard.

## Items
- [ ] `client/src/components/InventoryDetailModal.vue`, `client/src/components/BacklogDetailModal.vue`, `client/src/components/CostDetailModal.vue`, `client/src/components/ProductDetailModal.vue`, `client/src/components/ProfileDetailsModal.vue`, `client/src/components/TasksModal.vue` — add escape-to-close (listener added `onMounted` / removed `onUnmounted`, or gated on `isOpen` via a watcher to avoid leaks), body scroll lock, a focus trap plus focus-return-to-trigger, and `role="dialog"` `aria-modal` `aria-labelledby`.
- [ ] Same six modals — add an `aria-label` to each icon-only close button.
- [ ] `client/src/components/ProfileMenu.vue:6,97` — replace the `@blur` + `setTimeout(...,200)` close with a document click-outside listener; add `aria-haspopup`/`aria-expanded`, Escape-to-close, and arrow-key navigation.
- [ ] `client/src/components/LanguageSwitcher.vue:6,80` — same fix as ProfileMenu (click-outside listener, `aria-expanded`, Escape, arrow-key nav).
- [ ] `client/src/views/Dashboard.vue` — add `role`/`title`/`aria-label` to the SVG donut chart so it is announced.
- [ ] `client/src/views/*.vue` clickable table rows — the `<td @click>` rows use only inline `cursor` styling; make them keyboard-focusable and operable (tabindex + keydown, or a real button/link).

## Suggested approach
Build escape-to-close, scroll-lock, focus-trap, focus-return, and the ARIA attributes into a shared `useModal` composable (see `extract-shared-composables`) so all six modals are fixed at once; handle the dropdowns and the donut/rows separately.
