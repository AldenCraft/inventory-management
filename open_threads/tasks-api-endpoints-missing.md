# Tasks feature is silently broken — client calls task endpoints that don't exist on the server

**Status:** ⚪ open

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The client defines a full Tasks CRUD API (`getTasks`/`createTask`/`deleteTask`/`toggleTask`) against `/api/tasks*`, but `server/main.py` implements no task routes at all — every route in the server is a `@app.get`, and none is `/api/tasks`. So every task call 404s. The errors are caught and only `console.error`'d, so nothing surfaces to the user. Mock tasks injected by `useAuth` still render in the modal, masking the fact that the API side is entirely dead.

## Where
- `client/src/api.js:77-95` — `getTasks` (GET), `createTask` (POST), `deleteTask` (DELETE), `toggleTask` (PATCH) all target `/api/tasks*`.
- `server/main.py:124-305` — only `@app.get` routes exist; there is no POST/DELETE/PATCH anywhere, and no `/api/tasks` path at all.
- `client/src/App.vue:149` — `onMounted(loadTasks)` fires `GET /api/tasks` on load → 404.
- `client/src/App.vue:89-95` — `loadTasks` swallows the failure with `console.error('Failed to load tasks:', err)`.
- `client/src/App.vue:97-105` — `addTask` POSTs to the missing route → 404 → swallowed; `apiTasks` never grows.

## Repro
Open the app, open the Tasks modal from the profile menu, and add a task. Nothing is added to the list; the browser console shows `Failed to add task:` with a 404. Deleting/toggling an API-sourced task would fail the same way (only the mock tasks from `useAuth` respond, because they are handled purely in client state).

## Fix / acceptance criteria
- Either implement the task CRUD endpoints in `server/main.py` (GET/POST/DELETE/PATCH `/api/tasks`) backed by a data store, with a matching Pydantic model, so the client calls succeed and added tasks persist for the session; OR
- Remove the dead client calls in `client/src/api.js` and rework the Tasks modal in `App.vue` to operate purely on local state, with a clear TODO noting there is no backend.
- Whichever path: adding a task in the modal must visibly succeed (or fail loudly), not silently no-op.
