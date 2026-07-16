# Dashboard references a `<PurchaseOrderModal>` component that doesn't exist

**Status:** ⚪ open

Created: 2026-07-16, from a Playwright smoke test of the running app (all six nav tabs). Surfaced as a Vue warning logged on every Dashboard render. File:line references are from local `main` at HEAD `032c157` and may drift — re-locate before acting.

---

## The problem
`Dashboard.vue`'s template renders `<PurchaseOrderModal ...>`, but the component is never imported and isn't registered in the component's `components: {}` block, and no `PurchaseOrderModal.vue` exists in `client/src/components/`. So Vue logs `[Vue warn]: Failed to resolve component: PurchaseOrderModal` on every Overview render, and the element renders to nothing.

Everything else for the feature is wired up — reactive state (`showPOModal`, `selectedBacklogForPO`, `poModalMode`), the `openPOModal`/`viewPO`/`handlePOCreated` handlers, the "Create PO" / "View PO" buttons on the Inventory Shortages table, and the `createPurchaseOrder`/`getPurchaseOrderByBacklogItem` calls in `api.js`. Only the modal component itself is absent, so the whole flow dead-ends: clicking "Create PO" flips `showPOModal` to `true` and nothing appears.

This is the frontend twin of the backend gap already noted in `GUIDE.md` ("Restocking tab: backend stubbed but unwired") and mirrors the pattern in [[tasks-api-endpoints-missing]] — the client is built against a feature that was never finished on the other side. Worth resolving together.

## Where
- `client/src/views/Dashboard.vue:289-295` — `<PurchaseOrderModal :is-open="showPOModal" :backlog-item="selectedBacklogForPO" :mode="poModalMode" @close @po-created="handlePOCreated" />` in the template.
- `client/src/views/Dashboard.vue:305-313` — only `ProductDetailModal` and `BacklogDetailModal` are imported and registered; `PurchaseOrderModal` is neither.
- `client/src/views/Dashboard.vue:212-225` — the "Create PO" / "View PO" buttons that call `openPOModal(item)` / `viewPO(item)`.
- `client/src/views/Dashboard.vue:327-329, 653-672` — the `showPOModal`/`selectedBacklogForPO`/`poModalMode` state and the `openPOModal`/`viewPO`/`handlePOCreated` handlers.
- `client/src/api.js:97-104` — `createPurchaseOrder` (POST `/purchase-orders`) and `getPurchaseOrderByBacklogItem` (GET `/purchase-orders/{id}`); the server implements neither (see `GUIDE.md`).
- `client/src/components/` — no `PurchaseOrderModal.vue`.

## Repro
Open the Overview page and check the browser console: `[Vue warn]: Failed to resolve component: PurchaseOrderModal` fires on mount (and again on data load). Then click "Create PO" on any Inventory Shortages row — `showPOModal` goes true but no modal renders.

## Fix / acceptance criteria
- Either build `client/src/components/PurchaseOrderModal.vue` (import + register it in `Dashboard.vue`), matching the existing detail-modal conventions — props `is-open`/`backlog-item`/`mode`, `close` + `po-created` events, i18n, and the shared modal a11y pattern from [[modal-and-dropdown-accessibility]] — and back it with the PO endpoints the server is missing; OR
- If the restocking feature is out of scope for now, remove the dead `<PurchaseOrderModal>` element, the PO state/handlers, and the "Create PO" / "View PO" buttons (or disable them with a "coming soon" affordance) so no console warning fires and no button dead-ends.
- Either path: no unresolved-component warning on Dashboard render, and the "Create PO" button either opens a working modal or is clearly not actionable.
