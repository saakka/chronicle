/* ============================================================
   Chronicle Daily — "Where & When"
   A history guessing game. See a striking image + a cryptic clue,
   then guess WHERE (pin a flat map) and WHEN (slide a timeline).
   Scored TimeGuessr-style: 5000 location + 5000 time per round.
   Self-contained — no dependency on app.js or the 3D globe.
   The flat guess-map reuses the self-hosted earth.jpg texture.
   ============================================================ */
(function () {
  "use strict";

  /* ---- the round bank (curated; spans antiquity → modern, all continents) ----
     year: negative = BCE.  tol: year-guess tolerance (smaller = stricter).
     img: Wikimedia Commons search (a proper noun → a striking real photo). */
  const ROUNDS = [
    { name:"The Great Pyramid of Giza", country:"Egypt", lat:29.9792, lng:31.1342, year:-2560, tol:200,
      img:"Great Pyramid of Giza", clue:"Three mountains of cut stone rise from the desert — raised by a god-king to outlast eternity itself." },
    { name:"Stonehenge", country:"United Kingdom", lat:51.1789, lng:-1.8262, year:-2500, tol:350,
      img:"Stonehenge", clue:"Giant stones, hauled across a prehistoric land, stand in a ring aligned to the rising midsummer sun." },
    { name:"The Parthenon, Athens", country:"Greece", lat:37.9715, lng:23.7267, year:-438, tol:90,
      img:"Parthenon Athens", clue:"A marble temple to a warrior goddess crowns the sacred rock above the world's first democracy." },
    { name:"The Terracotta Army", country:"China", lat:34.3853, lng:109.2785, year:-210, tol:100,
      img:"Terracotta Army", clue:"Thousands of life-size clay soldiers stand in buried ranks, set to guard a tyrant into the afterlife." },
    { name:"Petra", country:"Jordan", lat:30.3285, lng:35.4444, year:-50, tol:220,
      img:"Al-Khazneh Petra", clue:"An entire city carved from rose-red cliffs, hidden at the end of a narrow desert canyon." },
    { name:"Pompeii", country:"Italy", lat:40.7497, lng:14.4869, year:79, tol:60,
      img:"Pompeii ruins", clue:"A bustling city is frozen mid-breath as a mountain buries it beneath a sky of fire and ash." },
    { name:"The Colosseum, Rome", country:"Italy", lat:41.8902, lng:12.4922, year:80, tol:70,
      img:"Colosseum", clue:"Fifty thousand spectators roar as men and beasts fight for their lives beneath the emperor's gaze." },
    { name:"Hagia Sophia", country:"Turkey", lat:41.0086, lng:28.9802, year:537, tol:90,
      img:"Hagia Sophia", clue:"A dome so vast it seems to hang from heaven — the unrivalled wonder of a Christian empire." },
    { name:"Borobudur", country:"Indonesia", lat:-7.6079, lng:110.2038, year:800, tol:150,
      img:"Borobudur", clue:"A mountain of terraced stone crowned by bell-shaped shrines, lost for centuries under ash and jungle." },
    { name:"Chichen Itza", country:"Mexico", lat:20.6843, lng:-88.5678, year:900, tol:200,
      img:"Chichen Itza", clue:"On a stepped pyramid, a serpent of shadow slithers down the stairs at the turn of each season." },
    { name:"Angkor Wat", country:"Cambodia", lat:13.4125, lng:103.8670, year:1150, tol:120,
      img:"Angkor Wat", clue:"The largest religious monument on Earth, raised from the jungle to the gods by a god-king." },
    { name:"The Forbidden City", country:"China", lat:39.9163, lng:116.3972, year:1420, tol:90,
      img:"Forbidden City", clue:"A walled city of golden roofs where an emperor ruled — its inner courts forbidden to common feet." },
    { name:"Machu Picchu", country:"Peru", lat:-13.1631, lng:-72.5450, year:1450, tol:120,
      img:"Machu Picchu", clue:"A royal city of green terraces hides in the clouds, abandoned to the jungle and lost to the world." },
    { name:"Moai of Easter Island", country:"Chile", lat:-27.1212, lng:-109.3667, year:1500, tol:250,
      img:"Moai", clue:"Giant carved heads stare inland from the loneliest inhabited island on the planet." },
    { name:"The Taj Mahal", country:"India", lat:27.1751, lng:78.0421, year:1648, tol:40,
      img:"Taj Mahal", clue:"An emperor pours a fortune into the world's most beautiful tomb — for the wife he could not save." },
    { name:"The Statue of Liberty", country:"United States of America", lat:40.6892, lng:-74.0445, year:1886, tol:20,
      img:"Statue of Liberty", clue:"A copper giantess lifts her torch over the harbor, greeting millions who arrive by sea to a new world." },
    { name:"The Eiffel Tower", country:"France", lat:48.8584, lng:2.2945, year:1889, tol:15,
      img:"Eiffel Tower", clue:"An iron lattice tower, mocked at first as a monstrosity, rises to become the symbol of a nation." },
    { name:"Christ the Redeemer", country:"Brazil", lat:-22.9519, lng:-43.2105, year:1931, tol:15,
      img:"Christ the Redeemer", clue:"Arms outstretched atop a peak, a stone savior watches over a city of beaches and carnival." },
    { name:"The Berlin Wall", country:"Germany", lat:52.5163, lng:13.3777, year:1961, tol:12,
      img:"Berlin Wall", clue:"Overnight, a great city is split by concrete and barbed wire, tearing families apart for a generation." },
    { name:"The Sydney Opera House", country:"Australia", lat:-33.8568, lng:151.2153, year:1973, tol:12,
      img:"Sydney Opera House", clue:"White concrete sails billow over a harbor — a design so daring it nearly bankrupts the state to finish." },
  ];

  const ROUND_MAX = 10000;   // 5000 location + 5000 time
  const N = 5;               // mysteries per daily game
  const YEAR_MIN = -3000, YEAR_MAX = 2025;

  /* ---------- math + scoring ---------- */
  function haversineKm(a, b) {
    const R = 6371, toR = Math.PI / 180;
    const dLat = (b.lat - a.lat) * toR, dLng = (b.lng - a.lng) * toR;
    const s = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * toR) * Math.cos(b.lat * toR) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(s)));
  }
  const scoreLoc  = (km)      => Math.round(5000 * Math.exp(-km / 1500));
  const scoreTime = (dy, tol) => Math.round(5000 * Math.exp(-Math.abs(dy) / tol));

  /* ---------- seeded RNG for the deterministic daily puzzle ---------- */
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function shuffleIdx(rng) {
    const idxs = ROUNDS.map((_, i) => i);
    for (let i = idxs.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      const t = idxs[i]; idxs[i] = idxs[j]; idxs[j] = t;
    }
    return idxs;
  }
  function dayNumber() {
    const DAY0 = Date.UTC(2026, 0, 1);
    return Math.floor((Date.now() - DAY0) / 86400000) + 1;
  }

  /* ---------- formatting ---------- */
  const fmtYear = (y) => (y < 0 ? Math.abs(y) + " BCE" : y + " CE");
  const fmtKm   = (km) => km < 1 ? "less than 1 km" : (km < 20 ? km.toFixed(0) + " km" : Math.round(km).toLocaleString() + " km");
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));

  /* ---------- image fetch (Wikimedia Commons; promise-cached) ---------- */
  const IMGC = new Map();
  function fetchHeroImage(query) {
    if (IMGC.has(query)) return IMGC.get(query);
    const p = (async () => {
      const params = new URLSearchParams({
        action: "query", format: "json", origin: "*", generator: "search",
        gsrsearch: query, gsrnamespace: "6", gsrlimit: "8",
        prop: "imageinfo", iiprop: "url|mime|size", iiurlwidth: "1280",
      });
      try {
        const r = await fetch("https://commons.wikimedia.org/w/api.php?" + params.toString());
        const d = await r.json();
        const pages = Object.values((d.query && d.query.pages) || {});
        const cand = pages
          .map((pg) => (pg.imageinfo && pg.imageinfo[0]) || {})
          .filter((i) => i.mime === "image/jpeg" && (i.thumburl || i.url) && (i.width || 0) >= 700);
        cand.sort((a, b) => (b.width * b.height) - (a.width * a.height));
        return cand[0] ? (cand[0].thumburl || cand[0].url) : null;
      } catch (e) { return null; }
    })();
    IMGC.set(query, p);
    return p;
  }

  /* ---------- state ---------- */
  let queue = [], idx = 0, total = 0, plays = [], mode = "daily", guess = null, locked = false;

  /* ---------- tiny DOM helpers ---------- */
  let game;
  const byId = (id) => document.getElementById(id);
  function setHTML(html) { destroyMap(); game.innerHTML = html; }
  function show() { game.hidden = false; document.body.classList.add("game-open"); window.scrollTo(0, 0); }
  function hide() { game.hidden = true; document.body.classList.remove("game-open"); }

  function toast(msg) {
    let t = byId("gd-toast");
    if (!t) { t = document.createElement("div"); t.id = "gd-toast"; t.className = "gd-toast"; document.body.appendChild(t); }
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("show"), 2600);
  }

  /* ---------- Leaflet maps (guess + reveal) ----------
     A real slippy map: crisp dark tiles at every zoom level, inertial pan,
     native pinch-zoom and a smooth zoom animation. Replaces the old
     fixed-texture pan/zoom, which blurred the moment you zoomed in. */
  const TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
  const TILE_OPTS = {
    subdomains: "abcd", maxZoom: 20,
    attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a> · &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  };
  // Contain vertical drag (no grey void above/below the world) while letting it wrap horizontally.
  const WORLD_BOUNDS = [[-85, -100000], [85, 100000]];
  const COMMON = { worldCopyJump: true, maxBounds: WORLD_BOUNDS, maxBoundsViscosity: 1, minZoom: 1, maxZoom: 16 };

  let lmap = null, guessMarker = null;
  function destroyMap() { if (lmap) { try { lmap.remove(); } catch (e) {} lmap = null; guessMarker = null; } }
  function pinIcon(cls) {
    return L.divIcon({ className: "gd-mk gd-mk-" + cls, html: '<span class="gd-mk-dot"></span>', iconSize: [22, 22], iconAnchor: [11, 11] });
  }
  const normLng = (lng) => ((((lng + 180) % 360) + 360) % 360) - 180;   // wrapped copies → [-180,180)

  // Guess map: click / tap anywhere to drop the pin; zoom + pan to place it precisely.
  function guessMapMarkup() { return '<div id="gd-map" class="gd-map gd-map-live"></div>'; }
  function setupGuessMap() {
    if (typeof L === "undefined" || !byId("gd-map")) return;
    const map = L.map("gd-map", Object.assign({
      center: [22, 6], zoom: 1, zoomControl: true, attributionControl: true,
      zoomSnap: 0.25, zoomDelta: 0.5, wheelPxPerZoomLevel: 90, wheelDebounceTime: 18,
      inertia: true, zoomAnimation: true, fadeAnimation: true,
    }, COMMON));
    L.tileLayer(TILE_URL, TILE_OPTS).addTo(map);
    map.zoomControl.setPosition("topright");
    map.on("click", (e) => { if (!locked) placeGuess(e.latlng); });
    lmap = map;
    setTimeout(() => { if (lmap === map) map.invalidateSize(); }, 60);
  }
  function placeGuess(latlng) {
    guess = { lat: latlng.lat, lng: normLng(latlng.lng) };
    if (!guessMarker) guessMarker = L.marker(latlng, { icon: pinIcon("guess"), keyboard: false, interactive: false }).addTo(lmap);
    else guessMarker.setLatLng(latlng);
    const lock = byId("gd-lock"); if (lock) { lock.disabled = false; lock.textContent = "Lock in guess"; }
  }

  // Reveal map: the guess + the truth, a dashed line between them, framed to fit both.
  function revealMapMarkup() { return '<div id="gd-revealmap" class="gd-map gd-map-static"></div>'; }
  function buildRevealMap(p) {
    if (typeof L === "undefined" || !byId("gd-revealmap")) return;
    const g = [p.glat, p.glng], t = [p.lat, p.lng];
    const map = L.map("gd-revealmap", Object.assign({
      zoomControl: false, attributionControl: true, scrollWheelZoom: false, zoomSnap: 0.25,
    }, COMMON));
    L.tileLayer(TILE_URL, TILE_OPTS).addTo(map);
    L.polyline([g, t], { color: "#ffd27a", weight: 2, opacity: .85, dashArray: "5 7", interactive: false }).addTo(map);
    L.marker(t, { icon: pinIcon("truth"), interactive: false }).addTo(map);
    L.marker(g, { icon: pinIcon("guess"), interactive: false }).addTo(map);
    lmap = map;
    const fit = () => map.fitBounds([g, t], { padding: [55, 55], maxZoom: 7, animate: false });
    fit();
    setTimeout(() => { if (lmap === map) { map.invalidateSize(); fit(); } }, 60);
  }

  /* ---------- intro ---------- */
  function renderIntro() {
    const day = dayNumber();
    const saved = loadDaily(day);
    const streak = getStreak();
    setHTML(
      '<button class="gd-exit" id="gd-exit">← Globe</button>' +
      '<div class="gd-intro">' +
        '<p class="gd-kicker">✦ Chronicle Daily ✦</p>' +
        '<h1 class="gd-title">Where &amp; When</h1>' +
        '<p class="gd-lede">A striking image, one cryptic clue. <b>Guess where on Earth it happened — and what year.</b> ' +
        'Five mysteries spanning all of human history. The closer you are, the higher you score.</p>' +
        '<div class="gd-cta-row">' +
          (saved
            ? '<button class="gd-btn gd-btn-primary" id="gd-see-today">See today\'s result</button>'
            : '<button class="gd-btn gd-btn-primary" id="gd-start-daily">▶ Play Daily #' + day + '</button>') +
          '<button class="gd-btn" id="gd-start-endless">∞ Endless practice</button>' +
        '</div>' +
        (streak.streak > 0 ? '<p class="gd-streak">🔥 ' + streak.streak + '-day streak</p>' : '') +
        '<p class="gd-foot">5 rounds · 10,000 points each · same daily puzzle for everyone</p>' +
      '</div>'
    );
    byId("gd-exit").onclick = hide;
    const sd = byId("gd-start-daily"); if (sd) sd.onclick = () => startGame("daily");
    const st = byId("gd-see-today"); if (st) st.onclick = () => renderResults(true);
    byId("gd-start-endless").onclick = () => startGame("endless");
  }

  /* ---------- game flow ---------- */
  function startGame(m) {
    mode = m;
    if (m === "daily") {
      const day = dayNumber();
      const saved = loadDaily(day);
      if (saved) { plays = saved.plays; total = saved.total; renderResults(true); return; }
      queue = shuffleIdx(mulberry32(day)).slice(0, N).map((i) => ROUNDS[i]);
    } else {
      queue = shuffleIdx(mulberry32((Math.floor(Date.now()) ^ (idx + 1)) >>> 0)).slice(0, N).map((i) => ROUNDS[i]);
    }
    idx = 0; total = 0; plays = [];
    loadRound();
  }

  function loadRound() {
    guess = null; locked = false;
    const r = queue[idx];
    setHTML(
      '<button class="gd-exit" id="gd-exit">← Quit</button>' +
      '<div class="gd-round">' +
        '<div class="gd-hero" id="gd-hero"><div class="gd-hero-load">summoning a mystery…</div>' +
          '<div class="gd-cluewrap"><p class="gd-roundno">' + (mode === "daily" ? "Daily" : "Endless") + ' · Mystery ' + (idx + 1) + ' of ' + N + '</p>' +
          '<p class="gd-clue">“' + esc(r.clue) + '”</p></div>' +
        '</div>' +
        '<div class="gd-guess">' +
          '<p class="gd-ask"><b>Where</b> on Earth did this happen? <span class="gd-hint">zoom in &amp; tap to place your pin</span></p>' +
          guessMapMarkup() +
          '<p class="gd-ask gd-ask-when"><b>When</b>? <span id="gd-year" class="gd-year">1000 CE</span></p>' +
          '<input type="range" id="gd-when" class="gd-when" min="' + YEAR_MIN + '" max="' + YEAR_MAX + '" step="1" value="1000">' +
          '<div class="gd-scale"><span>3000 BCE</span><span>1 CE</span><span>1000</span><span>2025</span></div>' +
          '<button class="gd-btn gd-btn-primary gd-lock" id="gd-lock" disabled>Drop a pin to lock in</button>' +
        '</div>' +
      '</div>'
    );
    byId("gd-exit").onclick = () => { if (confirmQuit()) hide(); };
    // image
    fetchHeroImage(r.img).then((url) => {
      if (queue[idx] !== r) return;            // moved on
      const hero = byId("gd-hero"); if (!hero) return;
      if (url) {
        const im = new Image();
        im.onload = () => { if (queue[idx] === r && byId("gd-hero")) { hero.style.backgroundImage = "url('" + url.replace(/'/g, "%27") + "')"; hero.classList.add("ready"); } };
        im.src = url;
      } else { hero.classList.add("ready"); }
      const l = hero.querySelector(".gd-hero-load"); if (l) l.remove();
    });
    // when slider
    const when = byId("gd-when"), yr = byId("gd-year");
    when.addEventListener("input", () => { yr.textContent = fmtYear(+when.value); });
    // where map — zoomable & pannable so the pin can be placed precisely
    setupGuessMap();
    byId("gd-lock").onclick = lockGuess;
  }

  function lockGuess() {
    if (!guess || locked) return;
    locked = true;
    const r = queue[idx];
    const gy = +byId("gd-when").value;
    const km = haversineKm(guess, r);
    const ls = scoreLoc(km), ts = scoreTime(gy - r.year, r.tol), rs = ls + ts;
    total += rs;
    plays.push({ name: r.name, country: r.country, year: r.year, gy: gy, km: km, ls: ls, ts: ts, rs: rs, lat: r.lat, lng: r.lng, glat: guess.lat, glng: guess.lng, clue: r.clue, img: r.img });
    renderReveal();
  }

  function bar(score, maxv) {
    const pct = Math.round((score / maxv) * 100);
    return '<span class="gd-bar"><span class="gd-bar-fill" style="width:' + pct + '%"></span></span>';
  }

  function renderReveal() {
    const p = plays[plays.length - 1];
    const last = idx === N - 1;
    setHTML(
      '<button class="gd-exit" id="gd-exit">← Quit</button>' +
      '<div class="gd-reveal">' +
        '<div class="gd-hero ready" id="gd-hero">' +
          '<div class="gd-cluewrap"><p class="gd-roundno">' + esc(fmtYear(p.year)) + ' · ' + esc(p.country) + '</p>' +
          '<h2 class="gd-answer">' + esc(p.name) + '</h2></div>' +
        '</div>' +
        '<div class="gd-scorecard">' +
          revealMapMarkup() +
          '<div class="gd-scoreline"><span>📍 ' + fmtKm(p.km) + ' away</span>' + bar(p.ls, 5000) + '<b>' + p.ls.toLocaleString() + '</b></div>' +
          '<div class="gd-scoreline"><span>🗓️ you said ' + esc(fmtYear(p.gy)) + ' · it was ' + esc(fmtYear(p.year)) + '</span>' + bar(p.ts, 5000) + '<b>' + p.ts.toLocaleString() + '</b></div>' +
          '<div class="gd-scoreline gd-scoreline-total"><span>Round score</span>' + bar(p.rs, ROUND_MAX) + '<b>' + p.rs.toLocaleString() + ' / ' + ROUND_MAX.toLocaleString() + '</b></div>' +
          '<button class="gd-btn gd-btn-primary" id="gd-next">' + (last ? "See your results →" : "Next mystery →") + '</button>' +
        '</div>' +
      '</div>'
    );
    buildRevealMap(p);
    // re-show the hero image for this round
    fetchHeroImage(p.img).then((url) => { const h = byId("gd-hero"); if (h && url) h.style.backgroundImage = "url('" + url.replace(/'/g, "%27") + "')"; });
    byId("gd-exit").onclick = () => { if (confirmQuit()) hide(); };
    byId("gd-next").onclick = () => { idx++; if (idx < N) loadRound(); else finishGame(); };
  }

  function tierEmoji(rs) {
    return rs >= 9000 ? "🟩" : rs >= 7000 ? "🟨" : rs >= 4000 ? "🟧" : rs >= 1500 ? "🟥" : "⬛";
  }

  function finishGame() {
    if (mode === "daily") { saveDaily(dayNumber(), { total: total, plays: plays }); bumpStreak(dayNumber()); }
    renderResults(false);
  }

  function renderResults(alreadyPlayed) {
    const day = dayNumber();
    const maxTotal = N * ROUND_MAX;
    const emojis = plays.map((p) => tierEmoji(p.rs)).join("");
    const pctTitle = total >= maxTotal * 0.8 ? "Master Chronologist" : total >= maxTotal * 0.6 ? "Seasoned Time Traveller"
      : total >= maxTotal * 0.4 ? "Budding Explorer" : "Wide-eyed Novice";
    let rows = "";
    plays.forEach((p, i) => {
      rows += '<div class="gd-result-row"><span class="gd-result-em">' + tierEmoji(p.rs) + '</span>' +
        '<span class="gd-result-name">' + (i + 1) + '. ' + esc(p.name) + '</span>' +
        '<span class="gd-result-score">' + p.rs.toLocaleString() + '</span></div>';
    });
    const streak = getStreak();
    setHTML(
      '<button class="gd-exit" id="gd-exit">← Globe</button>' +
      '<div class="gd-results">' +
        '<p class="gd-kicker">' + (mode === "daily" ? "Chronicle Daily #" + day : "Endless run") + (alreadyPlayed ? " · already played today" : "") + '</p>' +
        '<h1 class="gd-title">' + total.toLocaleString() + ' <span class="gd-of">/ ' + maxTotal.toLocaleString() + '</span></h1>' +
        '<p class="gd-rank">' + pctTitle + '</p>' +
        '<p class="gd-emojis">' + emojis + '</p>' +
        '<div class="gd-result-list">' + rows + '</div>' +
        (streak.streak > 0 ? '<p class="gd-streak">🔥 ' + streak.streak + '-day streak</p>' : '') +
        '<div class="gd-cta-row">' +
          '<button class="gd-btn gd-btn-primary" id="gd-share">📋 Share my score</button>' +
          '<button class="gd-btn" id="gd-endless">∞ Play endless</button>' +
          '<button class="gd-btn" id="gd-globe">🌍 Explore the globe</button>' +
        '</div>' +
        (alreadyPlayed ? '<p class="gd-foot">New mysteries every day — come back tomorrow.</p>' : '') +
      '</div>'
    );
    byId("gd-exit").onclick = hide;
    byId("gd-share").onclick = () => shareScore(day, emojis, maxTotal);
    byId("gd-endless").onclick = () => startGame("endless");
    byId("gd-globe").onclick = hide;
  }

  function shareScore(day, emojis, maxTotal) {
    const text = "Chronicle Daily #" + day + "  " + total.toLocaleString() + "/" + maxTotal.toLocaleString() + "\n" +
      emojis + "\nGuess where & when across all history:\n" + location.origin + location.pathname;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => toast("Score copied — paste it to a friend!"), () => fallbackCopy(text));
    } else { fallbackCopy(text); }
  }
  function fallbackCopy(text) {
    const ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); toast("Score copied — paste it to a friend!"); }
    catch (e) { toast("Copy failed — select and copy manually."); }
    document.body.removeChild(ta);
  }

  function confirmQuit() {
    return idx === 0 && !locked && plays.length === 0 ? true : window.confirm("Quit this game? Your progress will be lost.");
  }

  /* ---------- localStorage: daily result + streak ---------- */
  function loadDaily(day) {
    try { const v = localStorage.getItem("chronicle-daily-" + day); return v ? JSON.parse(v) : null; } catch (e) { return null; }
  }
  function saveDaily(day, data) { try { localStorage.setItem("chronicle-daily-" + day, JSON.stringify(data)); } catch (e) {} }
  function getStreak() { try { return JSON.parse(localStorage.getItem("chronicle-streak") || '{"last":0,"streak":0}'); } catch (e) { return { last: 0, streak: 0 }; } }
  function bumpStreak(day) {
    const s = getStreak();
    if (s.last === day) return;
    s.streak = (s.last === day - 1) ? s.streak + 1 : 1;
    s.last = day;
    try { localStorage.setItem("chronicle-streak", JSON.stringify(s)); } catch (e) {}
  }

  /* ---------- boot ---------- */
  function boot() {
    game = byId("game");
    if (!game) return;
    const btn = byId("play-btn");
    if (btn) btn.addEventListener("click", () => { show(); renderIntro(); });
    // deep link: #play opens the game directly
    if (location.hash === "#play") { show(); renderIntro(); }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
