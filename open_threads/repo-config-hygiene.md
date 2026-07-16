# Repo and config hygiene (uv.lock, .env.example, vite)

**Status:** ✅ Fixed by [#26](https://github.com/AldenCraft/inventory-management/pull/26) — merged 2026-07-16

Created: 2026-07-16, from a whole-app multi-agent review of the inventory-management repo (four parallel review agents), run against local `main` at HEAD `032c157`. File:line references are from that checkout and may drift — re-locate before acting.

---

## The problem
A few config-level issues: the uv lockfile is gitignored so backend installs float to the newest compatible versions, the empty `.env.example` gives a new dev no hint about the token `.mcp.json` requires, and there are two low-impact dev-only npm audit findings.

## Items
- [ ] `.gitignore:32-33` — `server/uv.lock` is ignored (both an explicit `uv.lock` entry and a broad `*.lock` glob) and is untracked; this is almost certainly unintentional and defeats uv reproducibility (every install floats to the newest compatible). Narrow the `*.lock` glob, drop the `uv.lock` line, and commit `server/uv.lock`.
- [ ] `.gitignore:17` — `client/package-lock.json` being gitignored IS intentional (registry-leak prevention per `CLAUDE.md`); leave it.
- [ ] `.env.example` (empty) vs `.mcp.json:20` — `.mcp.json` requires `${GITHUB_PERSONAL_ACCESS_TOKEN}` but `.env.example` is empty, so nothing tells a new dev which var to set; document `GITHUB_PERSONAL_ACCESS_TOKEN` there.
- [ ] `client/` npm audit — 2 dev-only findings (esbuild dev-server request-exfil advisory GHSA-67mh-4wv8-2f99 via vite 5.4.21 / esbuild 0.21.5); dev-server only, low real impact. Bump vite when convenient.

## Suggested approach
Narrow the `*.lock` glob and commit `server/uv.lock`; document `GITHUB_PERSONAL_ACCESS_TOKEN` in `.env.example`; bump vite opportunistically.
