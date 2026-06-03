# Chronicle — Overnight Autonomous Build Log

This file is the source of truth for the unattended loop. Read it first every iteration.

## STANDING EMPHASIS (added by Ahmad, ~02:30 — applies to EVERY iteration)
The north star is the **WOW effect**. With every change ask: does this make the
experience more breathtaking? Specifically:
- **Portals more epic** — cinematic light, motion, depth, drama (don't overdo to the point of slow/garish).
- **Most intriguing photos** — pick the most striking, surprising, beautiful images per era; cut the dull/generic.
- Polish transitions, typography, pacing, sound for an emotional, cinematic feel.
Run for ~8 more hours from 02:30.

## Mission (set by Ahmad, ~02:00)
Run autonomously following this process:

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

## NEXT PRIORITIES — content + design tailored to HISTORY GEEKS (Civ-V vibe), set ~by Ahmad
Wikimedia is broad/generic. Make it richer and more curated:
1. **Curated image sources** (better than generic Wikimedia): query open cultural-heritage APIs —
   Art Institute of Chicago (free, CORS, no key) + The Met Open Access (free, CORS, no key) for
   artworks/artifacts; Wikimedia as fallback. Bias toward paintings/artifacts → painterly, Civ-like feel.
2. **Civilopedia-depth content**: tune the era prompt so each era also yields a key figure/leader,
   a defining wonder/achievement, and a pivotal turning point. Specific, geeky, accurate.
3. **Design audit (game-like HUD)**: ornamental era frames, a "key figure · wonder · year" fact strip,
   optional era-territory map snippet, leader/portrait highlight, tech/wonder timeline markers.
Implement via the Phase-2 audit cycles; keep accuracy + the WOW feel.

## CHANGELOG (newest first — append every iteration)
- iter4 — LIVING PLANET: starfield background + blue atmosphere glow; continuous slow auto-rotation with damping that PAUSES on country-hover and resumes on leave (interactive). Portal delay set to 2.2s with a smoother 2s zoom-into-country. Recorded content/design direction (Civ-V / history-geek) above.
- iter3 — WOW pass on the portal: god-rays (rotating conic light), drifting embers, slow zoom-push, flourished label (✦ … ✦). Smarter photo selection: fetch 40 candidates, drop maps/flags/crests/diagrams, rank by size + aspect + relevance → striking images first. Verified visually (Egypt portal) + fetchImages returns clean results. Next Phase-2 ideas: per-era backdrop = best image (not just [0]); zoom globe-out on exit; richer era transition; "wow" audit.
- iter2 — Spot-checked Greece end to end via DOM: portal→journey renders (eras, Cover Flow, timeline) for a non-Arab country. All-countries pipeline validated. Next: more spot-checks, then Phase 2 audit cycles.
- iter1 — Opened globe to ALL countries (no filter); centroid-based zoom for any country;
  added ~22 bespoke world themes; default theme for the rest. Verified themeFor + no JS errors. Committing.
- baseline — Committed 672bdaf (portal + journey + themes + sound). Loop armed.
