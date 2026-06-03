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
0. **Bespoke per-country landmark portals (TOP PRIORITY, ongoing):** every country should get its
   OWN landmark silhouette. System built: `LANDMARKS` (SVG) + `LANDMARK_BY_COUNTRY` in app.js + `.landmark`
   CSS. ~18 iconic done (Eiffel, Taj, Big Ben, Colosseum, Fuji, Great Wall, St Basil's, Christ Redeemer,
   Opera House, Petra, Angkor, Burj, Parthenon, ziggurat, pyramids, skyline). EXPAND: add more landmark
   SVGs (Statue of Liberty, Sagrada Família/Alhambra, Brandenburg Gate, Machu Picchu, Hagia Sophia,
   Leaning Tower, Stonehenge, Christ the King, Petronas, etc.) and map many more countries. Keep regional
   motif as fallback only where no landmark exists yet.
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
- LEGENDS + FLUIDITY + BIGGER PHOTOS (Ahmad: "the legends cannot be summoned", "more fluid",
  "in the timeline page make the picture waay bigger"). Diagnosed legend failure = Gemini FREE tier
  20 req/day → 429 RESOURCE_EXHAUSTED (not a code bug). Fixes:
  (a) LEGENDS: server now tries Gemini first (free) then falls back to CLAUDE for /api/story AND
      /api/profile, flipping GEMINI_OK off after the first 429. Verified live end-to-end: legend renders
      6 beats ("Unification of Egypt: King Narmer…") via Claude fallback. Added Anthropic-format schemas
      + _claude_json/_gemini_json helpers.
  (b) BIGGER TIMELINE PHOTOS: Cover Flow covers 400px → min(58vh,90vw,600px); era text shrunk to a slim
      centered header (smaller title, 2-line clamp), top padding 20vh→5vh, album full-width, deeper
      perspective. Photo is now the hero. Verified (600px center cover).
  (c) FLUIDITY: ensureEraImages() dedupes + preloads neighbour eras (instant prev/next), warms era 0 during
      the dossier (instant timeline), and prefetchStory() warms the legend on button hover; openStory uses
      the cached/in-flight result. (Tool note: Gemini key is FREE tier 20/day, so Claude carries most calls.)
- AUDIT (5 iterations, Ahmad asked to find+fix bugs) — read whole codebase, checked runtime console
  (only expected WebGL-sandbox errors), fixed + verified each:
  1. goToEra() async race (slow image fetch clobbered a newer era) → bail if currentEra/journey changed.
     Story keyboard trap: Escape exited the whole journey leaving story stuck; arrows leaked to eras
     underneath → Escape now closes only the story, arrows blocked; IntersectionObserver disconnected.
  2. Dossier stale-overwrite: added a dossierToken so a slow profile/photo fetch for a previous country
     can't paint over a newer one (renderDossier + loadGallery both guarded); clear stale _sections.
  3. JUNK_IMAGE regex over-matched substrings (dropped Chartres, flagship, Mapuche, Planalto, Charter Oak;
     "Chartres Cathedral" returned ZERO images) → word boundaries. Lightbox now opens a 1280px derived
     thumb not the multi-MB original. Empty captions no longer render an empty dark bar. Verified live.
  4. 2D canvas globe: reset drag on pointercancel/lostpointercapture (could freeze the globe); throttle
     hover hit-testing to 1/frame; stop the render loop when canvas is replaced by chip fallback.
     Verified: cancelled drag still auto-rotates.
  5. Server: don't cache empty/garbled AI answers (history/profile/story) so a retry can recover;
     harden static path check (defence-in-depth, verified traversal blocked); /favicon.ico → 204;
     more content types; thematic 🌍 favicon. Verified: live /api/history Egypt = 200, 10 eras.
- iter9 — INTERACTIVE 2D-CANVAS GLOBE FALLBACK (Ahmad: "the landing needs to be like it was 3 hours
  ago, when it was interactive like radio garden"). Root cause confirmed: the in-app preview pane has
  WebGL DISABLED (canvas.getContext('webgl') === null), so globe.gl can't draw there — the user only
  ever saw the non-interactive static fallback. FIX: showFallback() now builds a real interactive globe
  on a 2D canvas (no WebGL): orthographic projection of the actual Natural-Earth country shapes, dark
  ocean sphere + graticule + soft atmosphere glow (Radio-Garden look), slow auto-rotate, DRAG to spin,
  hover-highlight a country (gold), hover-dwell 1.1s OR click to enter — wires into the same enterCountry
  pipeline (sets lastHoverLatLng/Subregion/Continent so the portal theme is correct). Falls back to a
  chip list only if the GeoJSON can't be fetched. The real 3D globe.gl path is untouched and still renders
  on the user's machine. Verified in-preview: canvas paints (center pixel = ocean), shapes loaded, and the
  hover-dwell auto-entered Egypt/portal end to end. Screenshot confirms the dark interactive globe.
- iter8 — CIV-VI VISUAL THEME EVERYWHERE + 2D PLANET FALLBACK (Ahmad shared a Civ VI "Create Game"
  screenshot: "use this theme everywhere", and "i can still not see a planet"). (1) Retheme: new
  :root palette — deep navy bg, parchment ink, gold trim, teal/green action; added Cinzel (Trajan-like
  caps) for display titles + EB Garamond body via Google Fonts. Applied to landing, dossier (navy
  gradient + teal "Enter the timeline" button w/ gold border), journey era panel (navy glass + gold
  frame), story (navy). Verified via computed styles (reliable; screenshots are stale in this preview).
  (2) PLANET FIX: the 3D globe needs WebGL, which the in-app preview disables — so the user (viewing
  the preview pane) never saw a planet. Added a 2D spinning-Earth fallback in showFallback(): a circular
  blue-marble texture with sphere shading + atmosphere glow + CSS spin (spin2d), plus a curated 40-country
  chip grid ("Choose a civilization to explore"). Now a planet ALWAYS shows on the landing, even without
  WebGL; the real 3D globe still renders on the user's machine. Hide tagline/drag-hint via #globe-view.no-webgl.
  Verified: 2D globe present + animating, Cinzel loaded, 40 chips, dossier theme correct.
- iter7 — GEOGRAPHY-NOW-STYLE COUNTRY DOSSIER (original content, not copied). New server `/api/profile`
  calls Gemini (gemini-2.5-flash, key in gemini-key.txt, git-ignored) for an ORIGINAL profile
  (overview/political/physical/demographics/culture/funFacts). Browser fuses REST Countries hard facts
  (flag, capital, population, area, region, languages, currency) + the Gemini profile into a #dossier
  page shown AFTER the portal, BEFORE the timeline ("Enter the timeline →"). Endpoint verified (Japan,
  HTTP 200). TODO: visually confirm the dossier render; consider Met/AIC images on the dossier too.
- iter6 — ALL COUNTRIES COVERED, no exception: added 9 sub-region silhouettes (mosque, pagoda, temple,
  acacia, cathedral, castle, palm, mountains, cedars) + LANDMARK_BY_SUBREGION (all 22 UN sub-regions) +
  PALETTE_BY_CONTINENT. themeFor now resolves bespoke→sub-region→default and captures SUBREGION/CONTINENT
  on hover, so every country shows a fitting landmark. Verified West Africa → acacia. LOOP TODO: keep
  promoting sub-region defaults into UNIQUE per-country icons (Statue of Liberty, Sagrada Família,
  Brandenburg Gate, Machu Picchu, Hagia Sophia, Pisa, Stonehenge, Petronas, Moai, Sphinx, etc.).
- iter5 — BESPOKE PER-COUNTRY PORTALS: new SVG landmark library (LANDMARKS) + LANDMARK_BY_COUNTRY map; portal renders the country's own landmark (falls back to regional motif). ~18 iconic landmarks done; verified France (Eiffel) + India (Taj) visually. Loop should keep adding landmarks toward full coverage.
- iter4 — LIVING PLANET: starfield background + blue atmosphere glow; continuous slow auto-rotation with damping that PAUSES on country-hover and resumes on leave (interactive). Portal delay set to 2.2s with a smoother 2s zoom-into-country. Recorded content/design direction (Civ-V / history-geek) above.
- iter3 — WOW pass on the portal: god-rays (rotating conic light), drifting embers, slow zoom-push, flourished label (✦ … ✦). Smarter photo selection: fetch 40 candidates, drop maps/flags/crests/diagrams, rank by size + aspect + relevance → striking images first. Verified visually (Egypt portal) + fetchImages returns clean results. Next Phase-2 ideas: per-era backdrop = best image (not just [0]); zoom globe-out on exit; richer era transition; "wow" audit.
- iter2 — Spot-checked Greece end to end via DOM: portal→journey renders (eras, Cover Flow, timeline) for a non-Arab country. All-countries pipeline validated. Next: more spot-checks, then Phase 2 audit cycles.
- iter1 — Opened globe to ALL countries (no filter); centroid-based zoom for any country;
  added ~22 bespoke world themes; default theme for the rest. Verified themeFor + no JS errors. Committing.
- baseline — Committed 672bdaf (portal + journey + themes + sound). Loop armed.
