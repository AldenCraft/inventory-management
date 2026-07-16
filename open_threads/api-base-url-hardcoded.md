# API base URL is hardcoded to localhost:8001 in the built bundle

**Status:** ✅ Fixed by [#11](https://github.com/AldenCraft/inventory-management/pull/11) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
The API client hardcodes `API_BASE_URL = 'http://localhost:8001/api'`. The README documents `npm run build` for production, but any bundle built that way still points every request at `localhost:8001`, so a deployed frontend can never reach a real backend. There is no environment-variable override.

## Where
- `client/src/api.js:3` — `const API_BASE_URL = 'http://localhost:8001/api'`

## Repro
1. `npm run build` and serve the output from any host other than the dev machine (or any port scheme that isn't `localhost:8001`).
2. Every API call goes to `http://localhost:8001/api` and fails; the app loads no data.

## Fix / acceptance criteria
- Read the base URL from `import.meta.env.VITE_API_BASE_URL` with a `http://localhost:8001/api` fallback for local dev.
- Document the variable in a `.env.example` (and the client README/CLAUDE.md) so production builds can point at the real backend.
---
