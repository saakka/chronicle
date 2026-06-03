# Chronicle — Overnight Autonomous Build Log

This file is the source of truth for the unattended loop. Read it first every iteration.

## Mission (set by Ahmad, ~02:00)
Run autonomously for ~6 hours following this process:

1. **Phase 1 — Coverage:** Add **all countries on Earth** to the globe (not just Arab
   League). Give each a **bespoke portal** (palette + landmark silhouette + arrival
   line). Era *content* is generated on demand by the API, so "content per country"
   = make sure generation works + the portal/theme is fitting. Do NOT pre-generate
   all ~195 countries (wasteful + costs API credits) — spot-check a handful.

2. **Phase 2 — Improve loop (repeat until morning):**
   a. Audit the site, write **5 enhancement recommendations** (append to CHANGELOG below).
   b. Implement the **top 3**.
   c. Commit. Re-audit → 5 new recommendations → top 3 → commit. Repeat.

## Operating rules
- Commit after every milestone (so everything is reviewable/revertible in the morning).
- Keep edits in `public/` + `server.py`; sync to `/tmp/histapp` for the preview only.
- Verify with code + DOM `preview_eval` checks (screenshots in this preview are flaky).
- Be economical with the API key (rely on cache; don't regenerate needlessly).
- Don't break working features (globe hover→portal→journey, sounds, Cover Flow).
- If blocked (permission prompt / rate limit / Mac asleep), it's fine — resume next wake.

## State / checklist (update each iteration)
- [x] Phase 1: all-countries globe coverage (removed Arab-only filter; all 177 polys hoverable)
- [~] Phase 1: palette + motif + label mapping (22 Arab + ~22 major world countries bespoke; rest = sensible default). EXPAND more during Phase 2.
- [~] Phase 1: spot-check non-Arab countries end to end — Greece ✓ (Minoan era, 6 photos, 10-era timeline). Do 2–3 more.
- [ ] Phase 1 TODO: add fallback hover-points for micro-states missing from the 110m dataset
- [ ] Phase 2 cycles begin

## CHANGELOG (newest first — append every iteration)
- iter2 — Spot-checked Greece end to end via DOM: portal→journey renders (eras, Cover Flow, timeline) for a non-Arab country. All-countries pipeline validated. Next: more spot-checks, then Phase 2 audit cycles.
- iter1 — Opened globe to ALL countries (no filter); centroid-based zoom for any country;
  added ~22 bespoke world themes; default theme for the rest. Verified themeFor + no JS errors. Committing.
- baseline — Committed 672bdaf (portal + journey + themes + sound). Loop armed.
