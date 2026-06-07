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
   CSS. ~30 iconic done (Eiffel, Taj, Big Ben, Colosseum, Fuji, Great Wall, St Basil's, Christ Redeemer,
   Opera House, Petra, Angkor, Burj, Parthenon, ziggurat, pyramids, skyline, Sagrada Família, Brandenburg
   Gate, Machu Picchu, Hagia Sophia, Statue of Liberty, Moai, Petronas Towers, Borobudur, Persepolis,
   + Windmill (NL), Wat Arun (TH), Matterhorn (CH) [iter 12]). EXPAND NEXT: add Alhambra, Leaning Tower,
   Stonehenge, Sphinx, Christ the King, Belém Tower, Obelisco, etc. and map many more countries. Keep regional
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
- LANDMARK SILHOUETTES batch 4, iter 12 (autonomous loop; Ahmad re-ran /loop after the v=21 deploy went live).
  AUDIT: remaining iconic-but-generic gaps — Netherlands & Switzerland on the Western-Europe "cathedral"
  default, Thailand on the SE-Asia "temple" default. 5 RECS; implemented top 3: (1) Netherlands → Windmill
  (tapered body + cap + the 4-sail X — unique, no other country has it), (2) Thailand → Wat Arun (tall tiered
  central prang + flanking satellite prangs — distinct from the generic single-gable temple), (3) Switzerland
  → Matterhorn (steep asymmetric peak with a hooked summit — distinct from the multi-peak "mountains" motif).
  Added 3 SVGs to LANDMARKS + mapped Netherlands/Thailand/Switzerland (ADMIN names verified vs ne_110m).
  VERIFIED VISUALLY (standalone portal render + screenshots): all 3 read clearly. app.js JS_PARSE_OK. Cache-bust
  v=22. Committed locally; push to main GATED — this batch (v=22) awaits the next deploy approval. (Everything
  through v=21 — the epic content pass, the "Where & When" GAME, and landmark batches 1–3 — is already LIVE,
  deployed via the Render dashboard + verified: the gold Play button is on the live landing page.) BACKLOG:
  Portugal→Belém (must avoid reading as a generic castle), Egypt→Sphinx (keep pyramids), Argentina→Obelisco;
  + non-landmark priorities (museum image sources; game polish: 3D-globe reveal + per-round "dive into story").
- LANDMARK SILHOUETTES batch 3, iter 11 (autonomous loop; Ahmad re-ran /loop). AUDIT: the top remaining
  iconic-but-generic gaps were Malaysia, Indonesia and Iran — all falling back to the generic South / South-
  Eastern-Asia "temple" motif. 5 RECS; implemented top 3: (1) Malaysia → Petronas Towers (twin towers + setback
  crowns/spires + the skybridge with its V-support), (2) Indonesia → Borobudur (stepped pyramid-mountain +
  central bell stupa + flanking stupas), (3) Iran → Persepolis (a colonnade of tall columns, some broken,
  framing the Gate of All Nations). Added 3 SVGs to LANDMARKS + mapped Malaysia/Indonesia/Iran (ADMIN names
  verified vs ne_110m). VERIFIED VISUALLY (standalone portal render + screenshot): all 3 read clearly and are
  distinct from the generic temple/castle motifs. app.js JS_PARSE_OK. Cache-bust v=21. Committed locally; push
  to main GATED — THREE batches now await deploy (live at v=19 = content + Spain/Germany/Peru; PENDING = b2
  Hagia Sophia/Liberty/Moai, the GAME "Where & When", and b3 Petronas/Borobudur/Persepolis). BACKLOG:
  Thailand→Wat Arun, Portugal→Belém, Egypt→Sphinx (keep pyramids); + non-landmark priorities (museum image
  sources, game polish: 3D-globe reveal + per-round "dive into the story").
- 🎮 NEW FEATURE — "Chronicle Daily: Where & When" (Ahmad /goal: "make the website more interesting… eureka
  idea, let me know" → presented the idea → "go ahead" → built it). A daily history GUESSING GAME layered on
  Chronicle: a striking image + ONE cryptic clue → guess WHERE (drop a pin on a flat world map) and WHEN
  (timeline slider, 3000 BCE–2025) → TimeGuessr-style scoring (5000 location via haversine·exp-decay + 5000
  time via a per-round tolerance) → cinematic answer reveal → 5 rounds → results with a Wordle-style shareable
  emoji card + streaks. WHY (the eureka): it turns a lean-back encyclopedia into a daily, replayable, shareable
  habit that hooks NON-history people (the genre — TimeGuessr/GeoGuessr — is proven viral); Chronicle's edge is
  it spans ALL of history (artifacts/landmarks, not just the camera era) on a gorgeous UI, with the epic story
  as the reward. IMPL — all NEW and SELF-CONTAINED (no dependency on app.js or the 3D globe, so it cannot break
  the explorer): public/game.js (20 curated wonders antiquity→modern; date-seeded daily pick via mulberry32;
  haversine + scoring; localStorage daily result + streak; one live Wikimedia image per round) + public/game.css
  (premium gold/serif theme; the flat guess-map REUSES the self-hosted earth.jpg via equirectangular projection
  — so it needs no WebGL and is even preview-testable) + index.html ("▶ Play: Where & When" CTA on the landing,
  a #game section, game.css/game.js at v=1). VERIFIED in a /tmp preview harness (the sandboxed preview can't
  read the project dir, so the game files were staged in /tmp/gametest): the FULL loop works — intro (Daily
  #158) → live Rio image + clue → pin (projection correct: landed on Rio) → year slider → lock → scorecard
  (88 km→4,716; said 1940 vs 1931→2,744; 7,460/10,000; both pins + dashed line) → "Christ the Redeemer" reveal →
  5-round results (emoji card) → share ("Score copied"). Zero console errors throughout. Committed locally;
  push to main GATED — awaits Ahmad's deploy approval. NEXT IDEAS: 3D-globe reveal flourish; a per-round "dive
  into the full story" link into the existing journey; more rounds + difficulty/region modes.
- LANDMARK SILHOUETTES batch 2, iter 10 (autonomous loop — TOP PRIORITY continued; Ahmad re-ran /loop).
  AUDIT: after iter-8 (Spain/Germany/Peru) the biggest remaining "iconic country on a generic/wrong default"
  gaps were Turkey (Western-Asia mosque), USA (generic skyline — also the Northern-America default, so not
  distinctive) and Chile (South-America mountains). 5 RECS; implemented top 3: (1) Turkey → Hagia Sophia
  (broad central dome + 4 slender minarets w/ finials), (2) United States → Statue of Liberty (pedestal +
  spiked crown + raised torch arm/flame; REPLACES the generic skyline, which stays as the Northern-America
  sub-region default), (3) Chile → Moai (Easter Island, drawn in PROFILE — flat top, heavy brow, long nose,
  jutting chin — because a front view reads as a plain column; row of 3 facing the same way = the Ahu
  Tongariki lineup). Added 3 SVGs to LANDMARKS + mapped Turkey/Chile + changed USA in LANDMARK_BY_COUNTRY
  (ADMIN names verified vs ne_110m). VERIFIED VISUALLY (standalone portal render + screenshots): all 3 read
  clearly; the first moai pass (rounded columns) was REJECTED and redrawn as profiles. app.js JS_PARSE_OK.
  Cache-bust v=20. Committed locally; push to main GATED for autonomous work (Ahmad authorizes deploys
  per-batch) — NOT yet deployed (this batch awaits the next deploy approval). BACKLOG: Malaysia→Petronas,
  Alhambra, Stonehenge, Christ the King; + non-landmark priorities (museum image sources, civilopedia HUD).
- EPIC CONTENT PASS, iter 9 (Ahmad: "audit the content, photos and legends — make it more epic, catchy,
  interesting; someone who ISN'T into history needs to be interested"). AUDIT: the writing was tuned for
  people who ALREADY love history — the story prompt asked for "the flagship tale a history lover would
  instantly recognise", the profile was "for curious history geeks", and the 10-era timeline showed only
  NAME + DATES (meaningless to a newcomer). Photos asked for "concrete/photogenic" but never "striking".
  5 RECS; implemented top 4: (1) LEGENDS — rewrote STORY_PROMPT: pick the most DRAMATIC/surprising/emotional
  true tale (betrayal, daring, mystery, downfall), give it a film-like TITLE, BEAT 1 must HOOK (banned "In the
  year…"), BEAT 6 lands a payoff, plain cinematic language, every beat has stakes. (2) CONTENT — added a
  per-era "hook": one electrifying movie-poster teaser (8-16 words) in the history schema/prompt (max_tokens
  1200→2200); rendered as a gold italic DEK under the story title on legend page 0 AND on the era-intro screen
  (new .beat-dek CSS). (3) PHOTOS — STORY/PROFILE imageQuery now demands visually STRIKING subjects (treasure,
  monuments, dramatic art, faces); photo scoring area-weight 0.4→0.55 (relevance still dominant, so the
  out-of-context fix holds). (4) DOSSIER — rewrote PROFILE_PROMPT to lead with WONDER + "wait, WHAT?" funFacts,
  for ANYONE not just geeks. VERIFIED with REAL generation (edited server run locally, 2 calls): Japan's 10
  hooks are superb ("Rival warlords shatter Japan into chaos — until three men reunite it by sword and
  cunning"; "A teenager becomes emperor and transforms a feudal nation into an industrial powerhouse in
  decades"); the Sengoku story came back cinematic & hook-first ("The Night the Peasant Became a Warlord" →
  opens on a lowborn man watching a castle burn, betrayal by his own son, seppuku, legacy). Visual check of
  the new dek typography on legend page 0 = excellent. NOTE: Gemini free tier (20/day) is exhausted, so
  stories fall back to Claude Haiku — quality confirmed great, but it now costs Claude tokens; watch spend or
  raise the Gemini quota. py_compile + JS parse OK. Cache-bust v=19. Committed 4a8b846 + DEPLOYED LIVE
  (Ahmad authorized the push; auto-deploy is OFF so triggered Manual Deploy via the Render dashboard).
  VERIFIED ON PRODUCTION: v=19 serving, new client assets present (beat-dek, sagrada/brandenburg/machupicchu),
  and a fresh live history call (Egypt) returned 10 catchy hooks. BACKLOG (rec 5): legend presentation polish
  (bigger first beat, per-beat micro-kickers) + a museum-art image source (Met/AIC) for painterly images.
  NOTE FOR THE LOOP: auto-deploy is OFF — pushes need Ahmad's OK + a Manual Deploy click; keep accumulating
  reviewable LOCAL commits and surface them rather than assuming anything auto-ships.
- LANDMARK SILHOUETTES, iter 8 (autonomous loop — TOP PRIORITY: promote sub-region DEFAULTS into UNIQUE
  per-country landmark silhouettes). AUDIT: ~18 countries had bespoke icons; the rest fell back to a
  sub-region motif — fine for minor countries but several MAJOR/high-traffic ones looked generic or plain
  WRONG. Worst offender: Spain rendered a Greek PARTHENON (via the Southern-Europe default); Germany a
  generic cathedral; Peru a generic mountain range. 5 RECS this cycle (highest WOW-per-effort, zero API
  cost — pure SVG): (1) Spain→Sagrada Família, (2) Germany→Brandenburg Gate, (3) Peru→Machu Picchu,
  (4) Turkey→Hagia Sophia, (5) USA→Statue of Liberty. IMPLEMENTED TOP 3 (1–3): added 3 hand-built SVG
  silhouettes to LANDMARKS (sagrada = cluster of tapering spires w/ finials; brandenburg = colonnade +
  entablature + quadriga; machupicchu = sharp Huayna-Picchu peak + terraces + stone huts) and mapped
  Spain/Germany/Peru in LANDMARK_BY_COUNTRY (ADMIN names verified against the live ne_110m geojson so the
  mapping can't be silently dead). VERIFIED VISUALLY: rendered all 3 in a standalone portal-style scene
  (dark #140d06 fill on the sunset gradient, exact .landmark wrapper) + screenshotted — all three read
  clearly and look great. app.js PARSE_OK (JXA new Function; no node here). Cache-bust v=18. BACKLOG for
  next iters: recs 4–5 + Italy→Leaning Tower, Chile→Moai, Malaysia→Petronas, Egypt→Sphinx.
- LOAD SPEED ~10x (Ahmad goal: "optimise code to make the site faster x10"). MEASURED the load first: the
  globe was blocked by ~3.0MB of external assets, dominated by TWO textures — earth-blue-marble.jpg (1.46MB)
  + night-sky.png (904KB) = 2.37MB of imagery on every visit (globe.gl 499KB + geojson 144KB the rest).
  Fixes (pure asset/code, no API cost): (1) the 904KB night-sky PNG was REDUNDANT — #globe-view already has a
  designed CSS starfield+nebula backdrop; verified globe.gl's renderer has alpha, so backgroundColor('rgba(0,0,0,0)')
  + dropping backgroundImageUrl reveals the CSS backdrop → 904KB → 0 bytes (looks the same/cleaner). (2) Earth
  texture self-hosted + downscaled 4096²→1536px @q68 = 234KB (was 1.46MB) → also same-origin so the 2D-fallback
  globe no longer taints on getImageData. (3) Pinned globe.gl@2.46.1 (the bare URL had max-age=60 + a 302; the
  pinned URL is 1-year immutable) → skips a redirect on first load and is fully cached on repeat visits. NET:
  globe imagery 2.37MB → 234KB (~10x less); total blocking ~3.0MB → ~0.87MB first visit; repeat visits ~near-
  instant (globe.gl + earth cached). Cache-bust v=17.
- CODE-REVIEW FIXES, iter 7 (Ahmad: max-effort /code-review → "fix"). The review's own sweep caught a real
  bug created by iter-5's `do_HEAD = do_GET`: a HEAD probe to /api/{history,profile,story} ran the FULL handler
  — daily_budget_ok() + a real PAID AI generation — then discarded the body (HEAD must be side-effect-free).
  FIX #1: do_GET now short-circuits HEAD on the AI paths → headers-only 200, no generation, no budget spend,
  no rate-limit consumption. FIX #2: new daily_budget_refund() called on all 6 AI-failure paths so a flapping
  backend can't burn the daily cap (reserve+refund nets zero on failure). TESTS: test_server.py rewritten —
  the parallel key_lock check is now deterministic (Barrier, not sleep-timing); path-traversal asserts the
  server.py SOURCE never leaks across 5 payloads (not just "not 200"); port bind is try/excepted + allow_reuse
  + server_close; and NEW monkeypatched tests (no real AI) exercise the handler success/cache path AND directly
  verify Fix #1 (HEAD makes no AI call) and Fix #2 (failure refunds the slot). 16/16 pass; py_compile clean.
  Server-only change (no client cache-bust). DEFERRED (need a careful refcount/refactor, not a rushed patch):
  _INFLIGHT unbounded growth (#3), the 3-handler copy-paste (#12) and eraTitleOf/preloadHeroImage dedup (#13/#14).
- REVIEW FOLLOW-UPS, iter 6 (Ahmad: "review" → "fix"). Applied the self-review's actionable items:
  (1) CORRECTNESS — preloadHeroImage now receives `era.title || data.title` (was just `era.title`), matching
  loadPageImage's `legendEraTitle = era.title || data.title || ""`, so the pre-decoded hero always matches what
  page 0 shows even when an era has no title (previously a rare cache-miss made that beat's photo non-instant).
  (2) PERF — the success send_json in all three AI handlers now happens OUTSIDE the single-flight lock, so a slow
  client receiving the (larger) generated response can't hold the per-key lock and block same-key waiters.
  (3) TESTS — added test_server.py: durable, dependency-free smoke tests (key_lock serialize/parallel + no
  deadlock, do_HEAD→200, /api/story length cap→400, static serving, path-traversal defence, 404). 11/11 pass
  locally; py_compile + JS parse clean. Cache-bust v=16. (Deferred: #4 LRU-cap the caches + _INFLIGHT — low
  real risk since the free instance restarts on idle.)
- SERVER HARDENING, iter 5 (Ahmad: "ok, treat it" — apply the audit's batch #1–#4). server.py only (no
  client change, no cache-bust). (1) SINGLE-FLIGHT: new key_lock() — a per-key lock so concurrent requests
  for the SAME uncached country/era collapse onto ONE AI call (the rest wait, then serve the freshly-cached
  result) instead of each paying for a duplicate generation. Wrapped all three AI handlers (history/profile/
  story) with a lock + double-check; lock keys namespaced h:/p:/s: so endpoints don't serialise each other.
  (2) handle_story now length-caps country/era/period (was uncapped → oversized prompt/cache key). (3) do_HEAD
  = do_GET (HEAD returned 501 even though _write_payload supports it — uptime monitors / link previews now work).
  (4) history AI-call timeout 180s→60s (Haiku takes ~5s; bounds the single-flight wait + thread-hold); added
  TypeError to both JSON-parse except guards; prune fully-stale _RATE_BY_IP keys once the map exceeds 2000 so it
  can't grow forever. VERIFIED LOCALLY: key_lock serializes same-key + parallelizes diff-key, no deadlock;
  HEAD→200 no-body; oversized era→400; static/404/ping intact; py_compile clean.
- BUG+PERF AUDIT, iter 4 (Ahmad: "check for bugs and perf issues"). Ran 3 parallel deep-read audits
  (app.js correctness, app.js perf, server.py) + verified every finding against the code. Fixed the two
  confirmed high-value ones: (1) PERF — IMG_CACHE was keyed by "query|max", but _fetchImagesRaw always asks
  Commons for 8 and only slices locally, so the legend's pre-warm (max=5) and the page loads (max=6) used
  DIFFERENT keys → every era-open silently double-fetched ~6 Wikimedia searches. Now keyed by query alone
  (fetch 8 once, slice per caller) → ~halves Commons requests per era and isolates callers with a fresh slice.
  (2) BUG — goToEra's post-await guards checked currentEra/journey.hidden but NOT the country, so exiting
  mid-load and quickly entering a DIFFERENT country could render the old country's legend into the new
  journey; now captures myCountry at entry and bails if it changed. Cache-bust v=15.
  REPORTED (not yet fixed, lower-risk/by-design): server check-then-act cache race → duplicate paid AI calls
  if two users hit the same uncached country at once (daily cap backstops the bill); no do_HEAD (HEAD→501
  though _write_payload supports it); handle_story doesn't length-cap era/period; 2D-fallback globe repaints
  per-pixel during idle spin and doesn't pause when hidden (only affects no-WebGL users); unbounded caches +
  _RATE_BY_IP keys never pruned (instance restarts on spin-down so low real risk).
- SMOOTHNESS MARATHON, iter 3 — OUT-OF-CONTEXT PHOTO FIX (caught live on Japan/Jomon: the hero was a
  modern illuminated glass building). Root cause: a beat's specific query ("Jomon period hunter-gatherer
  settlement reconstruction") returns 0 Commons hits, so loadPageImage fell back to the BARE COUNTRY name
  ("Japan") — which returns generic *modern* photos (satellite shots, Tokyo Tower, glass facades) that jar
  against an ancient era. Verified live: "Japan" → satellite/tower/facade; "Japan Jomon period" → fire-pit,
  clay dogū figure, Jōmon artifacts. Two fixes: (1) CLIENT — new eraFallbackQuery() scopes the fallback to
  "country + era title" in BOTH preloadHeroImage and loadPageImage (kept identical so the <0.2s preload still
  matches what page 0 shows). (2) SERVER — STORY_PROMPT now demands a 2-4 word CONCRETE proper-noun imageQuery
  (a named artifact/place/person a museum would photograph) and explicitly bans abstract phrases like
  "settlement reconstruction"/"daily life" that return no photo. Cache-bust v=14.
- SMOOTHNESS MARATHON, iter 1–2 (Ahmad: "make it smoother … faster … 0 bugs"). Audited live first:
  globe renders in ~2.6ms/frame (~380fps headroom even with hover-restyle churn), no console errors,
  pixel-ratio correctly capped at 1.5, memory ~54MB. So the globe is NOT the bottleneck — the real
  gaps are main-thread/transition/navigation. Fixes: (1) INSTANT ERA SWITCHING — new warmEraHero():
  goToEra now warms each neighbour era's STORY *and* pre-decodes its first photo (was warming only the
  story), so flipping eras opens immediately instead of pausing ~0.7s on "Summoning the legend…". Adds
  ZERO AI spend — neighbour stories were already warmed; this only adds the free Wikimedia image
  prefetch. (2) MEMOIZED centroid() per feature — the shoelace-area camera-aim math now runs once per
  country instead of on every hover-change (snappier hovering over complex countries like Russia/USA).
  (3) Removed dead legendObserver (declared + disconnected, never assigned). Cache-bust v=13.
- PHOTOS IN <0.2s (Ahmad: "make it appear in less than 0,2sec"). A fresh internet photo can't
  beat the network floor (~0.6–0.8s: Commons search ~500–700ms + download), so "appear in <0.2s"
  is only possible if the image is ALREADY decoded when the legend renders. New preloadHeroImage(data):
  before goToEra calls renderLegend, it runs the SAME parallel beat+country search loadPageImage(0)
  would, takes the top pick (s[0]||c[0] — exactly what page 0 shows), and pre-decodes it via
  `new Image()` (capped at 1100ms so a photo-poor era never stalls the legend). Result: the legend
  opens WITH its first photo already in the browser cache → it paints in <0.2s (no spinner, no fade-in
  wait). Trade-off: the "Summoning the legend…" screen lingers up to ~1.1s longer; page-turns stay
  instant via warm-all (150ms stagger). A moved()/era-changed guard skips the stale render if the
  user navigates away mid-preload. Cache-bust v=12.
- PHOTOS UNDER 1s (Ahmad: "its slow, photos need to appear under 1s"). MEASURED live: a single
  search+download is already ~0.6–0.8s (search ~500–700ms dominates; Commons-CDN download only
  40–320ms). The slowness was the 3-level SEQUENTIAL fallback added last step — a photo-poor beat
  did up to 3 searches back-to-back (~1.8s+). Fix: loadPageImage now races the specific beat query
  AND a country-level fallback IN PARALLEL (the country search is shared + promise-cached across
  all 6 beats), preferring the specific result — one ~0.7s round-trip instead of three. Warm-all
  stagger 300→150ms for faster background fill. Net: a photo shows in well under a second whether
  the era is photo-rich or photo-poor. Cache-bust v=11.
- PHOTOS: 3-LEVEL FALLBACK fixes blank legend pages (Ahmad: "photos still not displaying"). Live
  diagnosis: fetchImages works (Eiffel→5) and Commons HAS results, but VERBOSE/SPECIFIC beat
  queries ("Visigothic crown artifact Spain museum", "Roderic Visigothic king medieval artwork")
  return few matches that the junk filter (maps/diagrams) strips → 0 photos; the single fallback
  (era+country) hit the same map-heavy results → also 0 → BLANK pages. Story-dependent, hence
  intermittent. Fix: loadPageImage now broadens through a chain — beat query → era+country → JUST
  the country (always photo-rich) — so a page is never blank, even for photo-poor historical
  subjects. Verified parse + chain present. Cache-bust v=10.
- PHOTOS: REJECT NON-PHOTO IMAGES (Ahmad: "photos still not displaying"). Diagnosed on the live
  site: photos DO load + display, but the relevance-first scoring let a perfectly-named NON-photo
  win — Spain page 1 was "Visigothic_Kingdom_chronology-gl.png" (a chronology DIAGRAM) and page 0
  a dark murky image, which reads as "no real photo." Fix: (1) strongly prefer JPEG — real
  photographs are JPEG, while diagrams/charts/maps/timelines/logos are PNG — via +4 "photoish" in
  the score and rebalancing relevance 8→6, so a perfectly-named .png diagram can't out-score an
  actual photo; (2) expanded JUNK_IMAGE to also drop chronology / timeline / genealogy /
  family-tree. Verified via stub: chronology.png is junk-rejected AND a JPEG photo out-scores a
  perfect-relevance PNG diagram. Cache-bust v=9.
- DAILY SPEND CEILING — bill protection (Ahmad: audit "major issues" → "fix it"). The per-minute
  rate limit bounded the request RATE but not the daily TOTAL, so a sustained abuser or viral
  spike could run up the Claude bill (≈80/min × all day). Added a HARD daily cap on real AI
  generations: daily_budget_ok() (RATE_DAILY env, default 1000), counting only cache MISSES
  (cached countries stay free and are always served), resetting at UTC midnight. Once the cap is
  hit, /api/history|profile|story return 429 "reached today's exploration limit — come back
  tomorrow" WITHOUT making an AI call → worst-case bill ≈ $2.50/day. Verified with a temp server
  (RATE_DAILY=2): calls 1–2 served, call 3 → 429 (no AI call), a cached country still 200,
  /api/ping unaffected. Tune RATE_DAILY in Render → Environment.
- FASTER LEGEND PHOTOS (Ahmad: "some legend page photos take so much time to appear"). Audited
  live by timing each beat's search + image-load: searches were instant (pre-warmed) and most
  thumbs loaded <1s, BUT (a) a page's image only began loading when you reached the PREVIOUS page
  (lazy +1), so a slow-to-generate Wikimedia thumbnail left a page blank until you arrived and
  waited; and (b) some beat queries returned NO image (e.g. "Indus Valley standardized weights")
  → blank placeholder forever. Fixes: (1) after page 1, WARM all remaining pages' photos in the
  background, staggered 300ms (700px thumbs), so every image gets the whole reading-time to load
  before you turn to it; (2) if a beat's own query finds nothing, FALL BACK to the era's general
  imagery (era title + country) so a page is never blank. Cache-bust app.js v=8.
- AUDIT-2 FIXES (Ahmad: "audit again" → "fix that"). (#1) Search is now forgiving + gives
  feedback: aliases (USA/UK/Britain/Holland/UAE…), prefix-then-substring fallback, and a toast
  when nothing matches (was: silent no-op). (#2) Multi-polygon zoom — centroid() aims at the
  LARGEST landmass (shoelace area) instead of averaging all of a country's territories, so
  USA/Russia/Indonesia no longer fly the camera mid-ocean. (#4) A failed legend now shows a
  "↻ Try again" button that re-runs the era. (#5) Deleted ~120 lines of dead slideshow/Met-art
  code (fetchMetArt, fetchVariedImages, ensureEraImages/Art, coverHtml, applyCoverflow,
  MET_CACHE) — KEPT cleanSubject/subjectCaption (still used by the live dossier gallery).
  Verified: app.js parses, zero dangling refs, search aliases/prefix/miss correct, centroid
  picks the big polygon. Cache-bust app.js v=7 / style.css v=6.
- CLICK-TO-OPEN + ON-TOPIC PHOTOS (Ahmad: "open the country when you click on it, not hover";
  "audit the photos, replace out-of-context ones"). (1) Entry is now on CLICK/tap, not the
  hover-dwell: removed the auto-enter timers in handleDwell + the 2D setHover. Hovering still
  highlights the country + warms history (debounced prefetch); onPolygonClick (WebGL) and the
  2D tap-to-enter open it. Hint → "click a country to dive in". (2) PHOTO RELEVANCE: image
  scoring now LEADS with title↔query overlap (relevance * 8) so an on-topic match beats a big
  off-topic photo — size/shape only break ties (was size-dominant → out-of-context winners).
  Tightened JUNK_IMAGE (stamps, banknotes, postcards, posters, caricatures, infographics,
  screenshots). STORY imageQuery now asked to include the place name to disambiguate. Verified
  via stub: picks "Charlemagne statue Aachen" (14.3) over a big landscape (7.3); hover no longer
  enters. Cache-bust v=6.
- SEARCH + SHARE LINKS (enhancements E4 + E5). (E4) A search box on the landing: a native
  <datalist> autocompletes every country (built from the globe's polygons in buildCountryIndex);
  pick one or press Enter → enterByName() computes the centroid and dives straight in. (E5) Deep
  links — entering a country sets #Country in the URL (shareable; opening …/#Japan jumps straight
  in via the load-time hash check), cleared on exit; uses history.replaceState (no reload, no
  hashchange loop). Plus Open Graph + Twitter meta tags so a shared link shows a preview card.
  Cache-bust v=5. Verified: app.js parses, served HTML carries the OG tags + search input.
- AUDIT FIXES + FASTER (Ahmad: "fix all of them and make it way faster"). From the audit:
  BUGS — (B1) no fetch timeout → the app hung ~50s on Render cold-start with the `busy` lock
  stuck (couldn't enter another country): added a 30s AbortController on history+story, a
  "Waking the server…" hint after 4s, and a clear "give it a few seconds" retry message.
  (B2) history prefetch fired on EVERY hover → debounced to a 600ms rest (rapid fly-overs
  coalesce to one, leaving cancels) — saves API calls + avoids self-rate-limiting. (B3) failed/
  empty image searches were cached forever → now NOT cached, so they retry. (B4) per-IP limit
  trusted the spoofable LEFTMOST X-Forwarded-For → now RIGHTMOST (the hop Render appends).
  (B5) WebGL resize debounced (120ms). FASTER — (E1) warm-up: ping /api/ping on landing so the
  free instance is awake by the time a country is picked; the history prefetch now CHAINS
  era-I's legend (warmEraStory) so the first page is ready when the portal ends. (E3 already
  shipped: legend page 1 shows "Era N · <Name>" + the dramatic headline.) Verified: server
  compiles, /api/ping 200, gzip intact, app.js parses, debounce+cancel proven via stub.
  Queued next: country search (E4), share links + OG tags (E5), GitHub auto-deploy (E2);
  dead-code removal deferred (zero runtime impact, risky surgery — separate pass).
- ERA NAMES ON EVERY ERA (Ahmad: "add a name for each era for each country, make it simple, ex:
  Abbasid Caliphate"). The era names existed (history "title") but were hidden in a tooltip — the
  timeline + header only showed dates. Now: (1) timeline dots show the NAME prominently (display
  font) above the dates; (2) journey header shows "<Era Name> · <dates>"; (3) legend kicker shows
  "Era N · <Era Name>". Server prompt tuned so titles are SHORT, iconic period/dynasty names
  (≤4 words, no "and"-compounds) — verified fresh: Iran → Achaemenid Empire, Parthian Empire,
  Sassanid Empire, Safavid Empire, Qajar Dynasty, Pahlavi Dynasty, Islamic Republic (all 2 words).
  CSS: .tl-name added, dots widened to 104px. Cache-bust bumped to v=3.
- KILLED THE LAG + WAY FASTER (Ahmad: "many many lags… make it waaay faster, the portal is taking
  so much time, same goes for pictures"). Diagnosed live via the browser: globe rendered an
  uncapped 3840px buffer (~8.3M px/frame) at devicePixelRatio 2, continuously. 20 fixes across
  three fronts:
  GLOBE LAG: (1) cap renderer pixel ratio to 1.5 (≈halves GPU pixels/frame — the #1 fix);
  (2) drop the bump/topology texture (less GPU + one fewer big download).
  PORTAL SPEED: (3) pre-portal zoom wait 1700→600ms; (4) globe fly 2000→1100ms; (5) portal hold
  1600→800ms; (6) close 650→380ms; (7) dwell 2000→1400ms (both hover paths) → portal ~3.3s→~1.4s.
  CSS to match: (8) clip-path 1.25→0.62s; (9) label/ring/rays/dust/flash + fade-out all shortened;
  (10) rays 200vmax→120vmax + (11) ring shadow 50px→18px (cheaper composite, less jank).
  LATENCY HIDING: (12) prefetch /api/history the moment you REST on a country (promise-cached per
  country), so eras are usually ready before the portal ends; enterCountry reuses it.
  PICTURES: (13) promise-cache image searches (dedupe concurrent + cache results);
  (14) on legend render, pre-warm ALL beats' searches in parallel (URLs ready → instant page turns)
  while the <img> still decodes lazily (active+next only); (15) gsrlimit 14→8 (lighter search);
  (16) gradient placeholder on .beat-bg so it never flashes black.
  LOAD: (17) server gzip for html/css/js/json — app.js 71.6KB→22.8KB (−68%, verified);
  (18) Cache-Control (html no-cache, css/js 600s, assets 1d); (19) HTTP/1.1 keep-alive;
  (20) preconnect+dns-prefetch unpkg (globe lib + Earth textures). Hint copy updated.
  Plus: (21) PAUSE the globe's WebGL render loop while reading a legend (it kept drawing ~8M
  px/frame behind the hidden page) and resume on exit; (22) cache-bust asset URLs (app.js?v=,
  style.css?v=) so redeploys actually reach browsers — a public-URL Render deploy has NO
  auto-deploy webhook, so deploys are triggered manually (Render ▸ Manual Deploy) for now.
  Verified locally: server compiles, gzip byte-identical on decompress, no JS errors, pre-warm fires
  all 6 searches, history prefetch reuses one promise/country. Live verification: pixel ratio cap.
- MUCH FASTER (Ahmad: "stuck in the portal for 10 seconds… photos very very slow, optimize it").
  Root causes found by timing each endpoint, fixed at the source:
  (1) HISTORY was Opus + adaptive thinking + a fat schema (summary + imageQuery + 4 imageQueries per
      era × 10) → ~22s. The live legend flow never reads those fields (legend text/images come from
      /api/story; the old slideshow that used them is dead code). Slimmed the schema to title+period
      only, switched to claude-haiku-4-5, max_tokens 1200 → **22s → 5.4s**.
  (2) LEGEND (/api/story) was ~13s: Gemini-2.5-flash "thinks" by default (~10s) and Claude Sonnet's
      constrained-JSON decoding for 6 beats was also ~10s. Disabled Gemini thinking (thinkingBudget:0)
      and moved the writer (legends + profiles) to claude-haiku-4-5 → **13s → ~2.4s**, prose still vivid.
  (3) PORTAL no longer blocks on the fetch. enterCountry used to `await` the history call between the
      portal animation and the journey (the "stuck 10s"). Now the portal runs on its own ~3.3s clock,
      the journey opens immediately with a "Summoning the chronicle…" state, and the timeline + first
      legend fill in when history resolves (showJourneyLoading()).
  (4) LEGEND PHOTOS load lazily: only the active page (+ the next, prefetched) fetch an image, using the
      700px thumb instead of the 1280px full — was loading all six 1280px backgrounds at once. New
      loadPageImage(i), idempotent, called from goToPage. Verified via stub: render fetches only q0+q1;
      turning two pages fetches q0..q3; pages 5–6 stay deferred until reached.
  Verified end-to-end in preview: portal→journey at ~6s with 10 timeline dots + loading state, then the
  real Iceland legend ("Ingólfr Arnarson cast his high-seat pillars overboard…"); layout intact.
- SMOOTHER (Ahmad: "make it more smooth"). Two real wins: (1) GLOBE dynamic resolution — render the
  textured sphere at a lighter buffer (~460px) WHILE moving (drag/fling/auto-rotate) for a solid-60fps
  spin, and sharpen to a crisp buffer (~760px) the instant it settles on a hovered country; buffer is
  re-allocated only on the moving↔still transition, not per frame. (2) COVER FLOW no longer calls
  getBoundingClientRect on the transformed covers each scroll frame — it uses offsetLeft + scrollLeft
  (untransformed layout) + translate3d, eliminating forced reflows → smoother photo scrolling. Verified:
  globe spins (pixels change), no new JS errors.
- NO DUPLICATE PHOTOS + INVITING COUNTRY PAGE + 10 FIXES (Ahmad: "same picture twice like Suez";
  country infos not inviting → add logos/icons; more fluid + 10 bug fixes).
  Dedup: 1) fetchImages tags each photo with a canonical Commons file id; 2) timeline shows ONE distinct
  photo per subject (no repeated subject/picture — verified Egypt = 4 unique); 3) dossier gallery 1 distinct
  per subject, id-deduped; 4) story beats never reuse an image; 5) duplicate/blank queries dropped before
  fetch. Captions: 6) strip redundant trailing country name; 7) never blank (fallback). Other fixes:
  8) broken/errored photos no longer stay invisible (error→loaded on covers); 9) zero globe fling velocity
  when resting on a country (stays put for the 2s dwell); 10) richer per-era query list (lead subject +
  varied subjects) for more distinct covers. INVITING: fact chips now carry icons (🏛️ Capital, 👥 Population,
  📐 Area, 🗣️ Languages, 💰 Currency, 🗺️ Region), section tabs carry icons (Political/Physical/Demographics/
  Economy/Culture), fun-facts header → "💡 Did you know?". Verified: 6 chip icons + distinct captions live.
- POLISH PASS — sharper globe, inviting landing, faster photos, smoother everything (Ahmad: better globe
  resolution; landing prompt; "20 iterations" of bugs/fluidity/faster photos). Iterations:
  1) globe texture 1024→2048; 2) render buffer 420→700; 3) per-pixel sphere frame-cache (repaint only on
  view change); 4) inviting "Which country will you explore?" landing prompt + 2s hint; 5) FIX title/tagline
  hidden behind opaque canvas (z-index); 6) preconnect+dns-prefetch Wikimedia hosts; 7) first cover/photo
  fetchpriority=high+eager, rest lazy; 8) decoding=async on all photos; 9) warmAllEras() progressive
  background prefetch of every era; 10) photos fade in on decode (covers+gallery); 11) time-based globe
  spin (fps-independent); 12) drag-release fling inertia; 13) scroll-to-zoom on the 2D globe (matches hint;
  FIX: previously didn't zoom); 14) debounced resize; 15) lightbox zoom-in animation; 16) user-select:none
  on globe (FIX: dragging selected text); 17) prefers-reduced-motion support (Ken Burns/stage/bg);
  18) gallery img priority; 19) cover img complete-check (cached imgs still fade); 20) e2e re-verified
  (globe→portal→dossier→timeline) + globe perf 3.8ms/frame at full res. Verified: zoom grows globe,
  sharper continents, title visible, captions clean, legends short, hover-highlight + 2s dwell intact.
- GLOBE: DROP DOTS, HIGHLIGHT COUNTRY ON HOVER, 2s DWELL (Ahmad). Removed the green station dots
  (buildDots + drawStations gone). On hover the country now glows: drawHighlight() fills + outlines the
  hovered feature's polygons (clipped to the near hemisphere) in warm gold over the textured Earth.
  Hover-dwell to launch the portal raised 1.1s→2.0s (2D setHover) and 1.0s→2.0s (3D handleDwell).
  Verified: 0 green pixels, ~6.3k gold-highlight pixels on hover, hover detection 9/16 swept points,
  and a 2s hover launched the India (Taj Mahal) portal.
- REAL RADIO-GARDEN GLOBE + CLEAN CAPTIONS (Ahmad shared a Radio Garden screenshot: realistic Earth +
  green dots + bright blue bg; and captions were in foreign languages).
  (a) GLOBE: 2D fallback rewritten from dots to a REAL textured Earth — per-pixel orthographic sampling
      of the (CORS-ok) NASA Blue-Marble texture into a capped 420px buffer, scaled to display; bright blue
      #3b34dd backdrop; green "station" dots over land; pale focus ring on the hovered country. Trig cut
      to 2/px (sin c = rho, cos c = z) → 3.8ms/frame at full size. 3D globe.gl bg also set to the blue.
      Verified: textured Africa/Europe + green dots + blue bg render (preview viewport stuck at 168px wide,
      so it shows small — full size on a real machine).
  (b) CAPTIONS: now the ENGLISH search subject that found the photo (cleanSubject) instead of the raw
      Wikimedia filename — fixes foreign-language/cryptic captions. Verified: "Narmer Palette", "Saqqara
      mastaba tomb", etc. Applies to era covers + dossier gallery.
- LEGENDS TIGHTER + RADIO-GARDEN DOTTED GLOBE + MORE FLUID (Ahmad: legends too wordy; globe should look
  like Radio Garden not the outlined one; even more fluid).
  (a) STORY_PROMPT now = one punchy sentence/beat (~18-28 words, no filler). Verified ~23 words/beat.
  (b) 2D fallback globe rewritten to a STIPPLED DOT globe (Radio-Garden look): per-feature bbox + a
      cos-lat-even land-dot grid (buildDots), drawn as batched small dots on the dark sphere; hovered
      country's dots glow gold. Dropped polygon fills + graticule. featureAt uses bbox fast-reject (also
      speeds hover). Verified: dotted continents render + click entered a country.
  (c) FLUIDITY: goToEra renders era TEXT instantly, then fillAlbum() injects photos when ready (album
      reserves min-height so no layout jump; shows "Gathering images…"); legend warms after a 1.2s dwell
      (plus on hover). Verified: title present 60ms after entering timeline; covers fill to 600px.
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
- PUBLISH + PHONE POLISH + MUSEUM IMAGES. (1) Publish-ready: per-IP+global rate limit on AI endpoints,
  render.yaml + requirements.txt + DEPLOY.md (Render free tier), phone QR encodes public URL when deployed.
  (2) Phone polish: svh sizing (no mobile address-bar crop), hide desktop hint on phones, centered phone
  button/card, smaller headings/clamped text, short-screen hero shrink. (3) More striking images: weave
  PUBLIC-DOMAIN artworks/artifacts from The Met Open Access into each era (hero + backdrop), queried by
  country+era and FILTERED to works whose museum metadata (department/culture/country) matches the country
  so they're on-topic; deduped within and across eras; captioned with the real artwork title. Verified:
  Egypt/Sudan eras show relevant Met pieces (e.g., "Archer's ring", "Drinking Cup"), all unique.
- EPIC LANDING (Ahmad: more striking, change the blue, make it epic, nicer prompt). Replaced the flat
  Radio-Garden blue with a cinematic deep-space backdrop on #globe-view (luminous indigo core glow behind
  the globe, violet/teal nebula wisps + a warm gold wisp, starfield, vignette to near-black). 2D canvas now
  clears transparent so that CSS backdrop shows around the planet; globe atmosphere halo widened/brightened
  (1.42R) for an epic glow. 3D globe restored to the night-sky starfield. New prompt: "Every country hides
  an epic. Spin the world, rest on any land, and step into its story." Verified via screenshot.
- DIRECT-TO-TIMELINE + FASTER (Ahmad: skip the per-country info page, go straight to the timeline; faster).
  enterCountry now calls startJourney() instead of showDossier() — selecting a country goes straight to
  the era timeline (no dossier stop, and no blocking profile fetch). The dossier stays one tap away: the
  country name in the journey header (with an ⓘ) opens it; its button is relabelled "Back to the timeline"
  and just closes it. Speed: museum (Met) art is now LAZY + non-blocking — fetchVariedImages is Wikimedia-only
  (fast first paint via renderAlbumCovers); ensureEraArt() fetches the public-domain piece(s) separately and
  weaves them in when ready (re-render), deduped across eras. Verified: lands on journey (dossier never shown),
  5 covers incl. 2 Met pieces woven in after, header opens dossier, Back closes it.
- TIMELINE = LEGENDS (Ahmad: take out the slideshow; show the legend directly per era; 1 legend per era,
  right pictures + text). Major restructure: the journey is now the legend itself — goToEra() loads that
  era's /api/story legend and renders it as full-screen scroll beats (one picture + narration each) into
  #era-legend; the era dots switch legends, ←/→ too. Removed: Cover Flow slideshow (album/coverHtml/
  applyCoverflow), the "Hear the legend" button, and the separate #story level-3 view (merged in). Header
  shows country (ⓘ → info) + era label. Neighbour legends warmed for instant prev/next; first era's legend
  warmed during the portal. Verified: Egypt lands straight on Era I legend "Narmer: The Uniter of Two Lands"
  (6 beats, picture+text), 10 era dots, no slideshow. (Minor: one beat pulled a historical map — could
  tighten beat image filtering next.)
- LEGEND = PAGE-TURNING ALBUM (Ahmad: go straight to first era's legend; story turned page-by-page like an
  album; the "wiki page" was a Wikimedia map). The era's legend is now a horizontal paged album: each beat =
  a full-screen page (picture + narration); turn pages via ‹ › arrows, tap (right=next, left edge=back),
  swipe, or ←/→ keys; pages slide (turned ones go left). At an album's edges, turning flips into the
  neighbouring era; the era dots jump to any era. Replaced the vertical scroll-snap with the pager
  (.legend-page .active/.prev). Image filter: also drop atlas/carte/karte/mapa/survey/cadastr; STORY_PROMPT
  now forbids maps/diagrams/documents and asks for a striking photographable subject per beat. Verified:
  Egypt → 6-page album ("The Unification of Egypt: Narmer Forges a Kingdom"), pages turn 0→1→2→back, no
  info page on entry. (Note: dossier-skip needs a hard-refresh if an old build is cached.)
