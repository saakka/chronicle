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
    { name:"The Great Wall of China", country:"China", lat:40.4319, lng:116.5704, year:1450, tol:250,
      img:"Great Wall of China", clue:"A stone dragon of wall coils over the mountains, marching for thousands of miles." },
    { name:"Mont-Saint-Michel", country:"France", lat:48.6361, lng:-1.5115, year:1000, tol:250,
      img:"Mont Saint-Michel", clue:"A spired abbey crowns a rocky island, marooned by the rising tide twice a day." },
    { name:"Neuschwanstein Castle", country:"Germany", lat:47.5576, lng:10.7498, year:1886, tol:25,
      img:"Neuschwanstein Castle", clue:"A fairy-tale castle perches on an Alpine crag, built by a king the world called mad." },
    { name:"The Leaning Tower of Pisa", country:"Italy", lat:43.7230, lng:10.3966, year:1372, tol:130,
      img:"Leaning Tower of Pisa", clue:"A marble bell tower began to lean before it was even finished — and never stopped." },
    { name:"The Sagrada Família", country:"Spain", lat:41.4036, lng:2.1744, year:1882, tol:80,
      img:"Sagrada Familia", clue:"A forest of stone spires climbs to heaven — a basilica still unfinished after a century." },
    { name:"The Alhambra", country:"Spain", lat:37.1760, lng:-3.5881, year:1350, tol:150,
      img:"Alhambra Granada", clue:"A red-walled palace of carved arches and fountains, last jewel of a fading kingdom." },
    { name:"Big Ben (Elizabeth Tower)", country:"United Kingdom", lat:51.5007, lng:-0.1246, year:1859, tol:30,
      img:"Big Ben London", clue:"A great clock tower keeps watch over a riverside parliament in a foggy capital." },
    { name:"Notre-Dame de Paris", country:"France", lat:48.8530, lng:2.3499, year:1345, tol:150,
      img:"Notre-Dame de Paris", clue:"A Gothic cathedral of gargoyles and flying buttresses, nearly lost to flames in our own age." },
    { name:"The Pyramid of the Sun, Teotihuacan", country:"Mexico", lat:19.6925, lng:-98.8438, year:100, tol:200,
      img:"Teotihuacan", clue:"Along an Avenue of the Dead rises a great pyramid, in a city whose builders left no name." },
    { name:"The Petronas Towers", country:"Malaysia", lat:3.1579, lng:101.7117, year:1998, tol:12,
      img:"Petronas Towers", clue:"Twin silver towers, joined by a sky-bridge, were briefly the tallest on Earth." },
    { name:"The Burj Khalifa", country:"United Arab Emirates", lat:25.1972, lng:55.2744, year:2010, tol:8,
      img:"Burj Khalifa", clue:"A needle of glass spears the desert sky — the tallest thing humankind has ever built." },
    { name:"The Golden Gate Bridge", country:"United States of America", lat:37.8199, lng:-122.4783, year:1937, tol:15,
      img:"Golden Gate Bridge", clue:"A burnt-orange suspension bridge leaps across a fog-wreathed strait." },
    { name:"Mount Rushmore", country:"United States of America", lat:43.8791, lng:-103.4591, year:1941, tol:18,
      img:"Mount Rushmore", clue:"Four presidents stare from a granite cliff, each stone face taller than a house." },
    { name:"Itsukushima Shrine", country:"Japan", lat:34.2959, lng:132.3197, year:1168, tol:150,
      img:"Itsukushima torii", clue:"A vermilion gate stands in the sea, seeming to float before its shrine at high tide." },
    { name:"Himeji Castle", country:"Japan", lat:34.8394, lng:134.6939, year:1609, tol:90,
      img:"Himeji Castle", clue:"A white castle spreads its tiered roofs like a heron about to take flight." },
    { name:"Saint Basil's Cathedral", country:"Russia", lat:55.7525, lng:37.6231, year:1561, tol:90,
      img:"Saint Basil's Cathedral", clue:"Onion domes swirl in candy colors above a vast red square." },
    { name:"The Golden Temple", country:"India", lat:31.6200, lng:74.8765, year:1604, tol:100,
      img:"Golden Temple Amritsar", clue:"A gilded shrine floats on a sacred pool, open on all four sides to every traveler." },
    { name:"The Great Mosque of Djenné", country:"Mali", lat:13.9054, lng:-4.5556, year:1907, tol:130,
      img:"Great Mosque of Djenne", clue:"The greatest mud-brick building on Earth, bristling with beams, re-plastered by hand each year." },
    { name:"The Rock Churches of Lalibela", country:"Ethiopia", lat:12.0317, lng:39.0411, year:1200, tol:150,
      img:"Lalibela church", clue:"Churches carved downward into solid rock, hewn from the earth as if by angels." },
    { name:"Great Zimbabwe", country:"Zimbabwe", lat:-20.2674, lng:30.9337, year:1300, tol:200,
      img:"Great Zimbabwe", clue:"Vast curving walls of fitted stone, raised without mortar by a vanished African kingdom." },
    { name:"The Potala Palace", country:"China", lat:29.6558, lng:91.1171, year:1645, tol:120,
      img:"Potala Palace", clue:"A white-and-crimson palace climbs a holy hill in the highest country on Earth." },
    { name:"The Temples of Bagan", country:"Myanmar", lat:21.1722, lng:94.8585, year:1100, tol:150,
      img:"Bagan temples", clue:"Thousands of brick spires scatter across a misty plain, glowing at dawn." },
    { name:"Sigiriya", country:"Sri Lanka", lat:7.9570, lng:80.7603, year:480, tol:150,
      img:"Sigiriya", clue:"A king's palace crowns a sheer rock, reached by a stair through a lion's stone paws." },
    { name:"The Great Buddha of Kamakura", country:"Japan", lat:35.3169, lng:139.5358, year:1252, tol:100,
      img:"Great Buddha of Kamakura", clue:"A giant bronze Buddha sits in the open air, its temple long ago swept away by a wave." },
  ];

  const ROUND_MAX = 10000;   // 5000 location + 5000 time
  const N = 5;               // mysteries per daily game
  const ROUND_SECONDS = 60;  // per-round countdown — auto-submits at zero
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

  /* ---------- sound (self-contained WebAudio synth — no asset files; mutable) ---------- */
  const Snd = (() => {
    let ctx = null, master = null, muted = false;
    try { muted = localStorage.getItem("chronicle-muted") === "1"; } catch (e) {}
    function ensure() {
      if (ctx || ctx === false) return ctx || null;
      try {
        ctx = new (window.AudioContext || window.webkitAudioContext)();
        master = ctx.createGain(); master.gain.value = 0.5; master.connect(ctx.destination);
      } catch (e) { ctx = false; }
      return ctx || null;
    }
    function tone(c, freq, at, dur, o2) {
      o2 = o2 || {};
      const osc = c.createOscillator(), g = c.createGain();
      osc.type = o2.type || "sine";
      osc.frequency.setValueAtTime(freq, at);
      if (o2.slideTo) osc.frequency.exponentialRampToValueAtTime(o2.slideTo, at + dur);
      const peak = o2.gain || 0.18, atk = o2.attack || 0.006, rel = o2.release || 0.12;
      g.gain.setValueAtTime(0.0001, at);
      g.gain.exponentialRampToValueAtTime(peak, at + atk);
      g.gain.exponentialRampToValueAtTime(0.0001, at + dur + rel);
      osc.connect(g); g.connect(master);
      osc.start(at); osc.stop(at + dur + rel + 0.03);
    }
    const chord = (c, base, semis, step, dur, o2) => semis.forEach((n, i) => tone(c, base * Math.pow(2, n / 12), c.currentTime + i * step, dur, o2));
    return {
      get muted() { return muted; },
      resume() { const c = ensure(); if (c && c.state === "suspended") c.resume(); },
      toggleMute() { muted = !muted; try { localStorage.setItem("chronicle-muted", muted ? "1" : "0"); } catch (e) {} if (!muted) { this.resume(); this.blip(); } return muted; },
      play(fn) { const c = ensure(); if (c && !muted) fn(c); },
      place() { this.play((c) => { tone(c, 430, c.currentTime, 0.05, { type: "triangle", gain: 0.16 }); tone(c, 660, c.currentTime + 0.004, 0.05, { type: "triangle", gain: 0.1 }); }); },
      blip()  { this.play((c) => tone(c, 680, c.currentTime, 0.07, { type: "sine", gain: 0.18 })); },
      lock()  { this.play((c) => tone(c, 280, c.currentTime, 0.2, { type: "sawtooth", gain: 0.13, slideTo: 580 })); },
      tick()  { this.play((c) => tone(c, 880, c.currentTime, 0.025, { type: "square", gain: 0.05 })); },
      tickUrgent() { this.play((c) => tone(c, 1180, c.currentTime, 0.04, { type: "square", gain: 0.09 })); },
      timeout() { this.play((c) => tone(c, 240, c.currentTime, 0.4, { type: "sawtooth", gain: 0.14, slideTo: 110 })); },
      count() { this.play((c) => tone(c, 1320, c.currentTime, 0.014, { type: "sine", gain: 0.035 })); },
      reveal(q) { this.play((c) => chord(c, 330, q >= 0.8 ? [0,4,7,12] : q >= 0.5 ? [0,4,7] : q >= 0.25 ? [0,3,7] : [0,1,6], 0.06, 0.3, { type: "triangle", gain: 0.12 })); },
      fanfare(q) { this.play((c) => chord(c, 392, q >= 0.6 ? [0,4,7,12,16] : [0,3,7,10], 0.11, 0.34, { type: "triangle", gain: 0.14 })); },
    };
  })();

  /* ---------- animation helpers ---------- */
  const easeOut = (t) => 1 - Math.pow(1 - t, 3);
  function countUp(el, to, dur, sound) {
    const t0 = performance.now(); let lastBeep = 0;
    (function step(now) {
      const t = Math.min(1, (now - t0) / dur), v = Math.round(to * easeOut(t));
      el.textContent = v.toLocaleString();
      if (sound && t < 1 && t - lastBeep > 0.07) { Snd.count(); lastBeep = t; }
      if (t < 1) requestAnimationFrame(step); else el.textContent = to.toLocaleString();
    })(performance.now());
  }
  function animatePolyline(line, from, to, dur, onDone) {
    const t0 = performance.now();
    (function step(now) {
      const t = Math.min(1, (now - t0) / dur), e = easeOut(t);
      line.setLatLngs([from, [from[0] + (to[0] - from[0]) * e, from[1] + (to[1] - from[1]) * e]]);
      if (t < 1) requestAnimationFrame(step); else { line.setLatLngs([from, to]); if (onDone) onDone(); }
    })(performance.now());
  }

  /* ---------- hero images (curated Commons files, with a search fallback) ----------
     Each round pins one hand-picked, recognizable, LANDSCAPE photo (by exact Commons
     file title), resolved to a thumbnail at runtime. If a pinned file ever fails we
     fall back to the old name-search. Curation kills the misleading auto-picks the
     "biggest JPEG from a name search" used to surface — 19th-c. engravings, museum
     artifacts on black, city panoramas, and extreme-aspect images that cropped to a
     confusing slice (e.g. the Statue of Liberty showing only drapery). */
  const HERO_FILE = {
    "Great Pyramid of Giza": "File:The Great Pyramid of Giza from southeast corner.JPG",
    "Stonehenge": "File:Stonehenge, Condado de Wiltshire, Inglaterra, 2014-08-12, DD 18.JPG",
    "Parthenon Athens": "File:Parthenon, Acropolis, Athens, Greece.jpg",
    "Terracotta Army": "File:Terracotta Army, View of Pit 1.jpg",
    "Al-Khazneh Petra": "File:Petra , Al-Khazneh 2.jpg",
    "Pompeii ruins": "File:Pompeii Ruins (48440776966).jpg",
    "Colosseum": "File:Colosseum of Rome, Italy.jpg",
    "Hagia Sophia": "File:Hagia Sophia Mars 2013.jpg",
    "Borobudur": "File:Borobudur-Temple-Park Indonesia Stupas-of-Borobudur-11.jpg",
    "Chichen Itza": "File:Chichen Itza, El Castillo (14180679857).jpg",
    "Angkor Wat": "File:Angkor Wat with its reflection (cropped).jpg",
    "Forbidden City": "File:Beijing, Forbidden City, Hall of Supreme Harmony (6170352582).jpg",
    "Machu Picchu": "File:80 - Machu Picchu - Juin 2009 - edit.jpg",
    "Moai": "File:Easter Island, Ahu Tongariki (6696298947).jpg",
    "Taj Mahal": "File:Taj Mahal Sunset.jpg",
    "Statue of Liberty": "File:New York City (New York, USA), Statue of Liberty -- 2012 -- 6660.jpg",
    "Eiffel Tower": "File:Eiffel tower from trocadero.jpg",
    "Christ the Redeemer": "File:Christ the Redeemer-(Corcovado) side frontal view.jpg",
    "Berlin Wall": "File:East Side Gallery - Dmitri Vrubel - Le baiser (Berlin).jpg",
    "Sydney Opera House": "File:Sydney Harbour with view of Opera House on a cloudy day (50746511306).jpg",
    "Great Wall of China": "File:The Mutianyu section of the Great Wall of China.jpg",
    "Mont Saint-Michel": "File:Mont Saint Michel Abbey, Mont Saint-Michel, France, 2016-09-25, 01.jpg",
    "Neuschwanstein Castle": "File:Neuschwanstein Castle 2024.jpg",
    "Leaning Tower of Pisa": "File:The Duomo and Tower of Pisa at sunrise.jpg",
    "Sagrada Familia": "File:Sagrada familia-barcelona - panoramio (8).jpg",
    "Alhambra Granada": "File:Dusk Charles V Palace Alhambra Granada Andalusia Spain.jpg",
    "Big Ben London": "File:Big Ben at sunset - 2014-10-27 17-30.jpg",
    "Notre-Dame de Paris": "File:Paris, Notre Dame -- 2014 -- 1477.jpg",
    "Teotihuacan": "File:15-07-13-Teotihuacan-RalfR-WMA 0251.jpg",
    "Petronas Towers": "File:Kuala Lumpur Malaysia Petronas-Twin-Towers-01.jpg",
    "Burj Khalifa": "File:Dubai Skyline mit Burj Khalifa (18241030269).jpg",
    "Golden Gate Bridge": "File:Golden Gate Bridge as seen from Battery East.jpg",
    "Mount Rushmore": "File:Mount Rushmore detail view.jpg",
    "Itsukushima torii": "File:The Torii gate of the Itsukushima shrine- it gets partially submerged during high tide (49494998183).jpg",
    "Himeji Castle": "File:Himeji castle in may 2015.jpg",
    "Saint Basil's Cathedral": "File:Saint Basil's Cathedral, Red Square, Moscow, Russia.jpg",
    "Golden Temple Amritsar": "File:Hamandir Sahib (Golden Temple).jpg",
    "Great Mosque of Djenne": "File:Grand Mosque, Djenne (6863109).jpg",
    "Lalibela church": "File:The Bete Giyorgis.jpg",
    "Great Zimbabwe": "File:ASC Leiden - Rietveld Collection - East Africa 1975 - 05 - 033 - A wall of the ruins of Great Zimbabwe - Masvingo, Zimbabwe.jpg",
    "Potala Palace": "File:Potala.jpg",
    "Bagan temples": "File:20160801 Bagan temples 6743 DxO.jpg",
    "Sigiriya": "File:Sigiriya, Rock Fortress.jpg",
    "Great Buddha of Kamakura": "File:The Daibutsu or Great Buddha of Kamakura (9412296776).jpg",
  };
  const IMGC = new Map();
  async function resolveFile(file) {   // pinned Commons title → thumbnail URL
    const params = new URLSearchParams({
      action: "query", format: "json", origin: "*",
      titles: file, prop: "imageinfo", iiprop: "url", iiurlwidth: "1600",
    });
    try {
      const r = await fetch("https://commons.wikimedia.org/w/api.php?" + params.toString());
      const d = await r.json();
      const pg = Object.values((d.query && d.query.pages) || {})[0] || {};
      const ii = pg.imageinfo && pg.imageinfo[0];
      return ii ? (ii.thumburl || ii.url) : null;
    } catch (e) { return null; }
  }
  async function searchImage(query) {   // fallback: biggest on-topic JPEG by name
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
  }
  function fetchHeroImage(query) {   // promise-cached by query string
    if (IMGC.has(query)) return IMGC.get(query);
    const p = (async () => {
      const file = HERO_FILE[query];
      if (file) { const u = await resolveFile(file); if (u) return u; }   // curated pick
      return await searchImage(query);                                    // fallback
    })();
    IMGC.set(query, p);
    return p;
  }

  /* ---------- state ---------- */
  let queue = [], idx = 0, total = 0, plays = [], mode = "daily", guess = null, locked = false;
  let timerId = null, timeLeft = 0;

  /* ---------- tiny DOM helpers ---------- */
  let game;
  const byId = (id) => document.getElementById(id);
  function setHTML(html) { destroyMap(); stopTimer(); game.innerHTML = html; }
  function show() { game.hidden = false; document.body.classList.add("game-open"); window.scrollTo(0, 0); }
  function hide() { stopTimer(); game.hidden = true; document.body.classList.remove("game-open"); }

  function toast(msg) {
    let t = byId("gd-toast");
    if (!t) { t = document.createElement("div"); t.id = "gd-toast"; t.className = "gd-toast"; document.body.appendChild(t); }
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("show"), 2600);
  }

  /* ---------- per-round countdown (auto-submits at zero) ---------- */
  function stopTimer() { if (timerId) { clearInterval(timerId); timerId = null; } }
  function startTimer() {
    stopTimer();
    timeLeft = ROUND_SECONDS;
    updateTimerUI();
    timerId = setInterval(() => {
      timeLeft--;
      updateTimerUI();
      if (timeLeft > 0 && timeLeft <= 5) Snd.tickUrgent();
      else if (timeLeft > 0 && timeLeft <= 10) Snd.tick();
      if (timeLeft <= 0) { stopTimer(); onTimeUp(); }
    }, 1000);
  }
  function updateTimerUI() {
    const bar = byId("gd-timerbar"), num = byId("gd-timernum");
    if (!bar) return;
    bar.style.width = Math.max(0, timeLeft / ROUND_SECONDS * 100) + "%";
    bar.className = "gd-timerbar" + (timeLeft <= 10 ? " gd-timer-danger" : timeLeft <= 20 ? " gd-timer-warn" : "");
    if (num) { num.textContent = timeLeft + "s"; num.className = "gd-timernum" + (timeLeft <= 10 ? " gd-timer-danger" : timeLeft <= 20 ? " gd-timer-warn" : ""); }
  }
  function onTimeUp() {
    if (locked) return;
    Snd.timeout();
    toast("⏱ Time's up — locking in your guess.");
    lockGuess(true);   // force-submit whatever's set (no pin ⇒ 0 for location)
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
    // make the world cover the whole (possibly tall) container — no empty bands above/below
    const applyFill = () => {
      const s = map.getSize();
      const fill = Math.max(1, Math.log2(Math.max(s.x, s.y) / 256));
      map.setMinZoom(fill);
      if (map.getZoom() < fill) map.setView(map.getCenter(), fill, { animate: false });
    };
    map.on("resize", applyFill);
    lmap = map;
    setTimeout(() => { if (lmap === map) { map.invalidateSize(); applyFill(); } }, 60);
  }
  function placeGuess(latlng) {
    Snd.place();
    guess = { lat: latlng.lat, lng: normLng(latlng.lng) };
    if (!guessMarker) {
      guessMarker = L.marker(latlng, { icon: pinIcon("guess"), keyboard: false, draggable: true, autoPan: true }).addTo(lmap);
      guessMarker.on("dragend", () => { const ll = guessMarker.getLatLng(); guess = { lat: ll.lat, lng: normLng(ll.lng) }; Snd.place(); });
    } else guessMarker.setLatLng(latlng);
    const lock = byId("gd-lock"); if (lock) { lock.disabled = false; lock.textContent = "Lock in guess"; }
  }

  // Reveal map: the guess + the truth, a dashed line between them, framed to fit both.
  function revealMapMarkup() { return '<div id="gd-revealmap" class="gd-map gd-map-static"></div>'; }
  function buildRevealMap(p, onArrive) {
    if (typeof L === "undefined" || !byId("gd-revealmap")) { if (onArrive) onArrive(); return; }
    const hasGuess = p.glat != null && p.glng != null;
    const g = hasGuess ? [p.glat, p.glng] : null, t = [p.lat, p.lng];
    const map = L.map("gd-revealmap", Object.assign({
      zoomControl: false, attributionControl: true, scrollWheelZoom: false, zoomSnap: 0.25,
    }, COMMON));
    L.tileLayer(TILE_URL, TILE_OPTS).addTo(map);
    lmap = map;
    let line = null;
    if (hasGuess) {
      L.marker(g, { icon: pinIcon("guess"), interactive: false }).addTo(map);
      line = L.polyline([g, g], { color: "#ffd27a", weight: 2.5, opacity: .9, dashArray: "5 7", interactive: false }).addTo(map);
    }
    let done = false;
    const arrive = () => {   // drop the truth pin, then let the caller reveal the scores
      if (done || lmap !== map) return; done = true;
      L.marker(t, { icon: pinIcon("truth"), interactive: false }).addTo(map);
      if (onArrive) onArrive();
    };
    const frame = () => hasGuess ? map.fitBounds([g, t], { padding: [60, 60], maxZoom: 7 }) : map.setView(t, 4);
    setTimeout(() => {
      if (lmap !== map) return;
      map.invalidateSize();
      frame();   // animated fly to frame both points
      if (hasGuess && line) setTimeout(() => animatePolyline(line, g, t, 600, arrive), 760);
      else setTimeout(arrive, 700);
    }, 80);
    setTimeout(arrive, 2200);   // safety: never leave the scores stuck at 0
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
        '<div class="gd-timer"><div class="gd-timertrack"><div class="gd-timerbar" id="gd-timerbar"></div></div><span class="gd-timernum" id="gd-timernum">' + ROUND_SECONDS + 's</span></div>' +
        '<div class="gd-playarea">' +
          '<div class="gd-hero" id="gd-hero"><div class="gd-hero-load">summoning a mystery…</div>' +
            '<div class="gd-cluewrap"><p class="gd-roundno">' + (mode === "daily" ? "Daily" : "Endless") + ' · Mystery ' + (idx + 1) + ' of ' + N + '</p>' +
            '<p class="gd-clue">“' + esc(r.clue) + '”</p></div>' +
          '</div>' +
          '<div class="gd-mapwrap">' +
            '<p class="gd-ask gd-ask-where"><b>Where?</b> <span class="gd-hint">tap the map · drag the pin to fine-tune</span></p>' +
            guessMapMarkup() +
          '</div>' +
          '<div class="gd-when-block">' +
            '<p class="gd-ask gd-ask-when"><b>When?</b> <span id="gd-year" class="gd-year">1000 CE</span></p>' +
            '<input type="range" id="gd-when" class="gd-when" min="' + YEAR_MIN + '" max="' + YEAR_MAX + '" step="1" value="1000">' +
            '<div class="gd-scale"><span>3000 BCE</span><span>1 CE</span><span>1000</span><span>2025</span></div>' +
          '</div>' +
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
    byId("gd-lock").onclick = () => lockGuess();
    startTimer();
  }

  function lockGuess(force) {
    if (locked || (!guess && !force)) return;
    locked = true;
    stopTimer();
    Snd.lock();
    const r = queue[idx];
    const gy = +byId("gd-when").value;
    const km = guess ? haversineKm(guess, r) : null;   // no pin (timed out) ⇒ 0 for location
    const ls = guess ? scoreLoc(km) : 0;
    const ts = scoreTime(gy - r.year, r.tol), rs = ls + ts;
    total += rs;
    plays.push({ name: r.name, country: r.country, year: r.year, gy: gy, km: km, ls: ls, ts: ts, rs: rs, lat: r.lat, lng: r.lng, glat: guess ? guess.lat : null, glng: guess ? guess.lng : null, clue: r.clue, img: r.img });
    renderReveal();
  }

  function bar(score, maxv) {
    const pct = Math.round((score / maxv) * 100);
    return '<span class="gd-bar"><span class="gd-bar-fill" style="width:' + pct + '%"></span></span>';
  }

  function renderReveal() {
    const p = plays[plays.length - 1];
    const last = idx === N - 1;
    const barAt = (id) => '<span class="gd-bar"><span class="gd-bar-fill" id="' + id + '" style="width:0"></span></span>';
    setHTML(
      '<button class="gd-exit" id="gd-exit">← Quit</button>' +
      '<div class="gd-reveal">' +
        '<div class="gd-hero ready" id="gd-hero">' +
          '<div class="gd-cluewrap"><p class="gd-roundno">' + esc(fmtYear(p.year)) + ' · ' + esc(p.country) + '</p>' +
          '<h2 class="gd-answer">' + esc(p.name) + '</h2></div>' +
        '</div>' +
        '<div class="gd-scorecard">' +
          revealMapMarkup() +
          '<div class="gd-scoreline"><span>📍 ' + (p.km == null ? "No pin dropped" : fmtKm(p.km) + " away") + '</span>' + barAt("gd-fill-ls") + '<b class="gd-num" id="gd-ls">0</b></div>' +
          '<div class="gd-scoreline"><span>🗓️ you said ' + esc(fmtYear(p.gy)) + ' · it was ' + esc(fmtYear(p.year)) + '</span>' + barAt("gd-fill-ts") + '<b class="gd-num" id="gd-ts">0</b></div>' +
          '<div class="gd-scoreline gd-scoreline-total"><span>Round score</span>' + barAt("gd-fill-rs") + '<b><span class="gd-num" id="gd-rs">0</span> / ' + ROUND_MAX.toLocaleString() + '</b></div>' +
          '<button class="gd-btn gd-btn-primary" id="gd-next">' + (last ? "See your results →" : "Next mystery →") + '</button>' +
        '</div>' +
      '</div>'
    );
    // re-show the hero image for this round
    fetchHeroImage(p.img).then((url) => { const h = byId("gd-hero"); if (h && url) h.style.backgroundImage = "url('" + url.replace(/'/g, "%27") + "')"; });
    byId("gd-exit").onclick = () => { if (confirmQuit()) hide(); };
    byId("gd-next").onclick = () => { idx++; if (idx < N) loadRound(); else finishGame(); };
    // animate the map (fly → draw line → drop answer pin), then count the scores up
    buildRevealMap(p, () => { Snd.reveal(p.rs / ROUND_MAX); runScoreReveal(p); });
  }

  function runScoreReveal(p) {
    const steps = [
      ["gd-ls", "gd-fill-ls", p.ls, 5000],
      ["gd-ts", "gd-fill-ts", p.ts, 5000],
      ["gd-rs", "gd-fill-rs", p.rs, ROUND_MAX],
    ];
    steps.forEach((s, i) => setTimeout(() => {
      const fill = byId(s[1]); if (fill) fill.style.width = Math.round(s[2] / s[3] * 100) + "%";
      const num = byId(s[0]); if (num) countUp(num, s[2], 750, true);
    }, i * 720));
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
      rows += '<div class="gd-result-row" style="animation-delay:' + (0.2 + i * 0.12).toFixed(2) + 's"><span class="gd-result-em">' + tierEmoji(p.rs) + '</span>' +
        '<span class="gd-result-name">' + (i + 1) + '. ' + esc(p.name) + '</span>' +
        '<span class="gd-result-score">' + p.rs.toLocaleString() + '</span></div>';
    });
    const streak = getStreak();
    setHTML(
      '<button class="gd-exit" id="gd-exit">← Globe</button>' +
      '<div class="gd-results">' +
        '<p class="gd-kicker">' + (mode === "daily" ? "Chronicle Daily #" + day : "Endless run") + (alreadyPlayed ? " · already played today" : "") + '</p>' +
        '<h1 class="gd-title"><span id="gd-total">0</span> <span class="gd-of">/ ' + maxTotal.toLocaleString() + '</span></h1>' +
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
    const tn = byId("gd-total"); if (tn) countUp(tn, total, 1100, true);
    setTimeout(() => Snd.fanfare(maxTotal ? total / maxTotal : 0), 1150);
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
    if (!byId("gd-mute")) {   // persistent sound toggle (shown only while the game is open)
      const m = document.createElement("button");
      m.id = "gd-mute"; m.className = "gd-mute"; m.type = "button";
      m.setAttribute("aria-label", "Toggle sound");
      m.textContent = Snd.muted ? "🔇" : "🔊";
      m.onclick = () => { m.textContent = Snd.toggleMute() ? "🔇" : "🔊"; };
      document.body.appendChild(m);
    }
    const btn = byId("play-btn");
    if (btn) btn.addEventListener("click", () => { Snd.resume(); show(); renderIntro(); });
    // deep link: #play opens the game directly
    if (location.hash === "#play") { show(); renderIntro(); }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
