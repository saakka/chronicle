/* ---------------------------------------------------------------------------
   Chronicle — a planet of history
   Globe (hover a country ~1s) → themed PORTAL → immersive ERA JOURNEY.
   In the journey you travel era by era: image backdrop (Ken Burns), title +
   summary, a Cover Flow photo album, prev/next + a clickable timeline.
--------------------------------------------------------------------------- */

const globeView = document.getElementById("globe-view");
const globeFallback = document.getElementById("globe-fallback");

const portal = document.getElementById("portal");
const portalScene = document.getElementById("portal-scene");
const portalLabel = document.getElementById("portal-label");

const journey = document.getElementById("journey");
const bgA = document.getElementById("bg-a");
const bgB = document.getElementById("bg-b");
const eraStage = document.getElementById("era-stage");
const timeline = document.getElementById("timeline");
const navPrev = document.getElementById("nav-prev");
const navNext = document.getElementById("nav-next");
const exitBtn = document.getElementById("exit-btn");
const jCountry = document.getElementById("j-country");

const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightbox-img");
const lightboxCaption = document.getElementById("lightbox-caption");
const lightboxClose = lightbox.querySelector(".lightbox-close");
const toastEl = document.getElementById("toast");

/* ---- Arab countries (markers via shapes; tiny ones via hover spots) ---- */
const ARAB_COUNTRIES = [
  { country: "Algeria", lat: 28.0, lng: 2.6 },
  { country: "Bahrain", lat: 26.1, lng: 50.5 },
  { country: "Comoros", lat: -11.6, lng: 43.3 },
  { country: "Djibouti", lat: 11.8, lng: 42.6 },
  { country: "Egypt", lat: 26.8, lng: 30.8 },
  { country: "Iraq", lat: 33.2, lng: 43.7 },
  { country: "Jordan", lat: 31.0, lng: 36.2 },
  { country: "Kuwait", lat: 29.3, lng: 47.6 },
  { country: "Lebanon", lat: 33.9, lng: 35.9 },
  { country: "Libya", lat: 27.0, lng: 17.2 },
  { country: "Mauritania", lat: 20.3, lng: -10.4 },
  { country: "Morocco", lat: 31.8, lng: -6.5 },
  { country: "Oman", lat: 21.5, lng: 56.0 },
  { country: "Palestine", lat: 31.9, lng: 35.2 },
  { country: "Qatar", lat: 25.3, lng: 51.2 },
  { country: "Saudi Arabia", lat: 24.0, lng: 45.1 },
  { country: "Somalia", lat: 5.2, lng: 46.2 },
  { country: "Sudan", lat: 14.9, lng: 30.2 },
  { country: "Syria", lat: 34.8, lng: 38.0 },
  { country: "Tunisia", lat: 34.0, lng: 9.6 },
  { country: "United Arab Emirates", lat: 23.8, lng: 54.0 },
  { country: "Yemen", lat: 15.6, lng: 47.6 },
];
const ARAB_SET = new Set(ARAB_COUNTRIES.map((c) => c.country));
const FALLBACK_POINTS = ARAB_COUNTRIES.filter((c) => ["Bahrain", "Comoros"].includes(c.country));
const COUNTRIES_GEOJSON = "https://globe.gl/example/datasets/ne_110m_admin_0_countries.geojson";

/* ---- Portal themes (Egypt is bespoke; the rest fall back to a default) ---- */
/* Sky palettes — the mood you arrive into */
const PALETTES = {
  sand:  { sky: "linear-gradient(180deg, #241537 0%, #7d3b2e 42%, #c8702f 66%, #e7ad5b 84%, #f3cf92 100%)", sun: "#ffd98a", accent: "#ffcf57" },
  clay:  { sky: "linear-gradient(180deg, #281230 0%, #7a2f2a 44%, #b85433 70%, #de9356 100%)",               sun: "#ffc488", accent: "#ffb15a" },
  dusk:  { sky: "linear-gradient(180deg, #0c1030 0%, #33285e 44%, #7d5a86 74%, #d9af72 100%)",               sun: "#eccfa0", accent: "#d9b36b" },
  cedar: { sky: "linear-gradient(180deg, #0a1f28 0%, #1f4a3f 48%, #6f8a52 82%, #d9c47a 100%)",               sun: "#e7e3a6", accent: "#cdbf6a" },
  gulf:  { sky: "linear-gradient(180deg, #061f33 0%, #114f6a 48%, #3b8aa0 76%, #e7c47a 100%)",               sun: "#ffe6a8", accent: "#7ed0d8" },
};

/* Per-country: which landmark silhouette + palette + arrival line */
const COUNTRY_THEME = {
  "Egypt":               { palette: "sand",  motif: "pyramids", label: "Into the land of the Nile" },
  "Sudan":               { palette: "sand",  motif: "pyramids", label: "Into the kingdom of Kush" },
  "Saudi Arabia":        { palette: "sand",  motif: "dunes",    label: "Into the heart of Arabia" },
  "Algeria":             { palette: "sand",  motif: "dunes",    label: "Into the great Maghreb" },
  "Libya":               { palette: "sand",  motif: "columns",  label: "Into the shores of antiquity" },
  "Mauritania":          { palette: "sand",  motif: "dunes",    label: "Into the land of caravans" },
  "Tunisia":             { palette: "sand",  motif: "columns",  label: "Into the land of Carthage" },
  "Somalia":             { palette: "sand",  motif: "dunes",    label: "Into the land of Punt" },
  "Djibouti":            { palette: "sand",  motif: "dunes",    label: "Into the gate of tears" },
  "Morocco":             { palette: "clay",  motif: "mountains",label: "Into the kingdom of the far west" },
  "Jordan":              { palette: "clay",  motif: "columns",  label: "Into the rose-red realm" },
  "Yemen":               { palette: "clay",  motif: "towers",   label: "Into Arabia Felix" },
  "Oman":                { palette: "clay",  motif: "dome",     label: "Into the land of frankincense" },
  "Iraq":                { palette: "dusk",  motif: "ziggurat", label: "Into the cradle of civilization" },
  "Syria":               { palette: "dusk",  motif: "columns",  label: "Into the crossroads of empires" },
  "Palestine":           { palette: "dusk",  motif: "dome",     label: "Into the holy land" },
  "Lebanon":             { palette: "cedar", motif: "cedars",   label: "Into the land of the cedars" },
  "Comoros":             { palette: "cedar", motif: "mountains",label: "Into the perfumed isles" },
  "United Arab Emirates":{ palette: "gulf",  motif: "skyline",  label: "Into the shimmering Gulf" },
  "Qatar":               { palette: "gulf",  motif: "skyline",  label: "Into the pearl coast" },
  "Bahrain":             { palette: "gulf",  motif: "skyline",  label: "Into the isle of two seas" },
  "Kuwait":              { palette: "gulf",  motif: "skyline",  label: "Into the harbor of the Gulf" },
};

/* Bespoke themes beyond the Arab world (expanded over the night; default covers the rest) */
Object.assign(COUNTRY_THEME, {
  "Greece":        { palette: "dusk",  motif: "columns",  label: "Into the cradle of democracy" },
  "Italy":         { palette: "dusk",  motif: "columns",  label: "Into the heart of Rome" },
  "Turkey":        { palette: "dusk",  motif: "dome",     label: "Where East meets West" },
  "Iran":          { palette: "dusk",  motif: "dome",     label: "Into the land of Persia" },
  "Spain":         { palette: "clay",  motif: "columns",  label: "Into the Iberian crossroads" },
  "France":        { palette: "gulf",  motif: "towers",   label: "Into the land of light" },
  "Germany":       { palette: "dusk",  motif: "towers",   label: "Into the heart of Europe" },
  "United Kingdom":{ palette: "gulf",  motif: "skyline",  label: "Into the isles of empire" },
  "Russia":        { palette: "dusk",  motif: "dome",     label: "Into the vast north" },
  "China":         { palette: "clay",  motif: "mountains",label: "Into the Middle Kingdom" },
  "Japan":         { palette: "clay",  motif: "mountains",label: "Into the land of the rising sun" },
  "India":         { palette: "clay",  motif: "dome",     label: "Into the jewel of the East" },
  "Cambodia":      { palette: "cedar", motif: "dome",     label: "Into the empire of Angkor" },
  "Indonesia":     { palette: "cedar", motif: "mountains",label: "Into the thousand isles" },
  "Mexico":        { palette: "clay",  motif: "pyramids", label: "Into the land of the feathered serpent" },
  "Peru":          { palette: "clay",  motif: "mountains",label: "Into the realm of the Inca" },
  "Brazil":        { palette: "cedar", motif: "mountains",label: "Into the heart of the Amazon" },
  "United States of America": { palette: "gulf", motif: "skyline", label: "Into the new world" },
  "Ethiopia":      { palette: "cedar", motif: "mountains",label: "Into the highlands of Abyssinia" },
  "Nigeria":       { palette: "cedar", motif: "skyline",  label: "Into the giant of Africa" },
  "South Africa":  { palette: "clay",  motif: "mountains",label: "Into the cape of good hope" },
  "Australia":     { palette: "gulf",  motif: "skyline",  label: "Into the great south land" },
});

function themeFor(country) {
  const t = COUNTRY_THEME[country] || { palette: "dusk", motif: "mountains", label: "Into " + country };
  const p = PALETTES[t.palette] || PALETTES.dusk;
  return { sky: p.sky, sun: p.sun, accent: p.accent, motif: t.motif, label: t.label };
}

let world = null;
let globeControls = null;
let busy = false;            // a portal/journey is active
let currentCountry = "";
let currentEras = [];
let currentEra = 0;
let bgActiveEl = null;

let polyHoverFeat = null;
let polyHoverCountry = null;
let pointHoverCountry = null;
let lastHoverLatLng = null;
let dwellCountry = null;
let dwellTimer = null;

/* ====================== GLOBE ====================== */

function initGlobe() {
  const el = document.getElementById("globe");
  if (typeof Globe === "undefined" || !el) return showFallback();

  try {
    world = Globe()(el)
      .backgroundImageUrl("https://unpkg.com/three-globe/example/img/night-sky.png")
      .globeImageUrl("https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg")
      .bumpImageUrl("https://unpkg.com/three-globe/example/img/earth-topology.png")
      .showAtmosphere(true)
      .atmosphereColor("#7fb2ff")
      .atmosphereAltitude(0.22)
      .pointsData(FALLBACK_POINTS)
      .pointLat("lat").pointLng("lng")
      .pointColor(() => "rgba(255,207,87,0)")
      .pointRadius(0.7).pointAltitude(0.01)
      .pointLabel("country")
      .onPointHover((pt) => {
        pointHoverCountry = pt ? pt.country : null;
        if (pt) lastHoverLatLng = { lat: pt.lat, lng: pt.lng };
        recomputeHover();
      });
  } catch (err) {
    console.error("Globe init failed:", err);
    return showFallback();
  }

  sizeGlobe();
  globeControls = world.controls();
  globeControls.autoRotate = true;          // a living, always-turning planet
  globeControls.autoRotateSpeed = 0.35;
  globeControls.minDistance = 180;
  globeControls.enableDamping = true;       // smooth, weighty feel
  globeControls.dampingFactor = 0.1;
  world.pointOfView({ lat: 24, lng: 42, altitude: 2.1 }, 0);

  // Rotation pauses while you rest on a country (recomputeHover) and resumes after.
  window.addEventListener("resize", sizeGlobe);

  loadCountryShapes();
}

function loadCountryShapes() {
  fetch(COUNTRIES_GEOJSON)
    .then((r) => r.json())
    .then((gj) => {
      const polys = gj.features || []; // ALL countries on Earth
      world
        .polygonsData(polys)
        .polygonAltitude(0.008)   // flat — no "popping up" on hover
        .polygonCapColor((d) => (d === polyHoverFeat ? "rgba(201,162,75,0.5)" : "rgba(201,162,75,0.02)"))
        .polygonSideColor(() => "rgba(201,162,75,0.06)")
        .polygonStrokeColor((d) => (d === polyHoverFeat ? "rgba(227,201,138,0.95)" : "rgba(201,162,75,0.16)"))
        .polygonLabel((d) => d.properties.ADMIN)
        .onPolygonHover((feat) => {
          polyHoverFeat = feat || null;
          polyHoverCountry = feat ? feat.properties.ADMIN : null;
          if (feat) lastHoverLatLng = centroid(feat);
          refreshPolygonStyles();
          recomputeHover();
        });
    })
    .catch((err) => console.error("Country shapes failed to load:", err));
}

function refreshPolygonStyles() {
  if (!world) return;
  world
    .polygonCapColor((d) => (d === polyHoverFeat ? "rgba(201,162,75,0.5)" : "rgba(201,162,75,0.02)"))
    .polygonStrokeColor((d) => (d === polyHoverFeat ? "rgba(227,201,138,0.95)" : "rgba(201,162,75,0.18)"));
}

function sizeGlobe() { if (world) world.width(window.innerWidth).height(window.innerHeight); }

function showFallback() {
  if (!globeFallback) return;
  globeFallback.hidden = false;
  globeFallback.innerHTML =
    '<div class="fallback-inner"><p>Choose a country:</p><div class="fallback-list">' +
    ARAB_COUNTRIES.map((c) => '<button class="chip" data-country="' + esc(c.country) + '">' + esc(c.country) + "</button>").join("") +
    "</div></div>";
}

/* ====================== HOVER DWELL ====================== */

function recomputeHover() {
  const c = polyHoverCountry || pointHoverCountry || null;
  // Pause the living rotation while the user focuses a country; resume when they leave.
  if (globeControls && !busy) globeControls.autoRotate = !c;
  handleDwell(c);
}

function handleDwell(country) {
  if (busy) return;
  if (globeControls && globeControls.autoRotate) return; // wait until the attract-spin stops
  if (country === dwellCountry) return;
  dwellCountry = country;
  clearTimeout(dwellTimer);
  if (country) {
    dwellTimer = setTimeout(() => {
      if (dwellCountry === country && !busy) enterCountry(country);
    }, 1000);
  }
}

/* ====================== PORTAL ====================== */

function playPortal(country) {
  const theme = themeFor(country);
  portalScene.style.background = theme.sky;
  portal.style.setProperty("--accent", theme.accent);
  portal.style.setProperty("--sun", theme.sun);
  portalScene.innerHTML = '<div class="sun"></div><div class="motif motif-' + theme.motif + '"></div>';
  portalLabel.textContent = theme.label;

  portal.hidden = false;
  portal.classList.remove("done");
  void portal.offsetWidth;       // reflow so the transition runs
  portal.classList.add("open");
  Sound.portal();
  return wait(1600);
}

function endPortal() {
  portal.classList.add("done");
  setTimeout(() => { portal.hidden = true; portal.classList.remove("open", "done"); }, 650);
}

/* ====================== ENTER A COUNTRY ====================== */

async function enterCountry(country) {
  if (busy) return;
  busy = true;
  currentCountry = country;
  currentEras = [];
  currentEra = 0;

  // 1. cinematic zoom: fly the globe down toward the country
  const loc = lastHoverLatLng || ARAB_COUNTRIES.find((c) => c.country === country) || null;
  if (world && loc) world.pointOfView({ lat: loc.lat, lng: loc.lng, altitude: 0.62 }, 2000);

  // fetch in parallel with the zoom
  const fetchPromise = (async () => {
    try {
      const res = await fetch("/api/history?country=" + encodeURIComponent(country));
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || "Something went wrong.");
      return { data: j };
    } catch (err) {
      return { error: err instanceof TypeError ? new Error("Can't reach the server.") : err };
    }
  })();

  await wait(2200);                       // 2.2s cinematic zoom before the portal opens
  const portalDone = playPortal(country); // portal opens over the zoomed globe
  const { data, error } = await fetchPromise;
  await portalDone;

  if (error || !data || !Array.isArray(data.eras) || !data.eras.length) {
    endPortal();
    busy = false;
    if (world) world.pointOfView({ lat: 24, lng: 42, altitude: 2.1 }, 900);
    toast(error ? error.message : "No history found. Try another country.");
    return;
  }

  currentEras = data.eras;
  if (data.demo) toast("Demo mode — built-in Egypt sample. Add an API key for any country.");

  // Reveal the journey behind the portal, then fade the portal away.
  globeView.style.display = "none";
  journey.hidden = false;
  jCountry.textContent = country;
  bgActiveEl = null;
  buildTimeline();
  await goToEra(0);
  endPortal();
  Sound.startAmbient();
}

/* ====================== ERA JOURNEY ====================== */

async function goToEra(index) {
  if (index < 0 || index >= currentEras.length) return;
  currentEra = index;
  const era = currentEras[index];
  updateTimeline();
  updateArrows();

  if (era.images === undefined) {
    era.images = await fetchImages(era.imageQuery || era.title, 6);
  }

  // backdrop (crossfade between two layers + Ken Burns)
  const bgUrl = era.images[0] ? era.images[0].thumb : null;
  setBackdrop(bgUrl);

  // stage content, animated in
  eraStage.classList.remove("show");
  eraStage.innerHTML = stageHtml(era, index);
  void eraStage.offsetWidth;
  eraStage.classList.add("show");

  const album = eraStage.querySelector(".album");
  if (album) {
    const update = () => applyCoverflow(album);
    album.addEventListener("scroll", () => requestAnimationFrame(update), { passive: true });
    album.querySelectorAll("img").forEach((img) => img.addEventListener("load", update));
    requestAnimationFrame(update);
    setTimeout(update, 350);
  }
}

function stageHtml(era, index) {
  const images = Array.isArray(era.images) ? era.images : [];
  return (
    '<div class="era-copy">' +
      '<div class="era-eyebrow">Era ' + toRoman(index + 1) + " · " + esc(era.period || "") + "</div>" +
      '<h2 class="era-h">' + esc(era.title || "") + "</h2>" +
      '<p class="era-p">' + esc(era.summary || "") + "</p>" +
    "</div>" +
    (images.length
      ? '<div class="album">' + images.map(coverHtml).join("") + "</div>"
      : '<p class="album-empty">No archive images found for this era.</p>')
  );
}

function setBackdrop(url) {
  const next = bgActiveEl === bgA ? bgB : bgA;
  next.style.backgroundImage = url ? "url('" + url.replace(/'/g, "%27") + "')" : "none";
  next.classList.remove("active");
  void next.offsetWidth;
  next.classList.add("active");
  if (bgActiveEl) bgActiveEl.classList.remove("active");
  bgActiveEl = next;
}

function buildTimeline() {
  timeline.innerHTML = currentEras
    .map((e, i) =>
      '<button class="tl-dot" data-go="' + i + '" title="' + esc(e.title || "") + '">' +
        '<span class="tl-num">' + toRoman(i + 1) + "</span>" +
        '<span class="tl-period">' + esc(e.period || "") + "</span>" +
      "</button>"
    )
    .join("");
}

function updateTimeline() {
  const dots = timeline.querySelectorAll(".tl-dot");
  dots.forEach((d, i) => d.classList.toggle("active", i === currentEra));
  const active = dots[currentEra];
  if (active && active.scrollIntoView) active.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
}

function updateArrows() {
  navPrev.disabled = currentEra <= 0;
  navNext.disabled = currentEra >= currentEras.length - 1;
}

function exitJourney() {
  Sound.stopAmbient();
  journey.hidden = true;
  busy = false;
  dwellCountry = null;
  clearTimeout(dwellTimer);
  polyHoverFeat = null; polyHoverCountry = null; pointHoverCountry = null;
  refreshPolygonStyles();
  globeView.style.display = "";
  sizeGlobe();
  if (world) world.pointOfView({ lat: 24, lng: 42, altitude: 2.1 }, 900); // zoom back out
  if (globeControls) globeControls.autoRotate = true;                     // resume the living spin
}

function travelTo(index) {
  if (index < 0 || index >= currentEras.length || index === currentEra) return;
  Sound.chime();
  goToEra(index);
}

navPrev.addEventListener("click", () => travelTo(currentEra - 1));
navNext.addEventListener("click", () => travelTo(currentEra + 1));
exitBtn.addEventListener("click", exitJourney);

timeline.addEventListener("click", (e) => {
  const dot = e.target.closest("[data-go]");
  if (dot) travelTo(parseInt(dot.getAttribute("data-go"), 10));
});

document.addEventListener("keydown", (e) => {
  if (!lightbox.hidden) { if (e.key === "Escape") closeLightbox(); return; }
  if (journey.hidden) return;
  if (e.key === "ArrowRight") travelTo(currentEra + 1);
  else if (e.key === "ArrowLeft") travelTo(currentEra - 1);
  else if (e.key === "Escape") exitJourney();
});

/* fallback chips on the globe still route here */
document.addEventListener("click", (e) => {
  const c = e.target.closest("[data-country]");
  if (c) return enterCountry(c.getAttribute("data-country"));
  const fig = e.target.closest(".cover");
  if (fig && eraStage.contains(fig)) openLightbox(fig.getAttribute("data-full"), fig.getAttribute("data-caption"));
});

/* ====================== WIKIMEDIA IMAGES (browser-side) ====================== */

// Drop the dull stuff (maps, flags, crests, diagrams, locator dots) — we want
// striking photographs and artworks.
const JUNK_IMAGE = /(map|locator|flag|coat[\s_-]?of[\s_-]?arms|\bseal\b|emblem|logo|diagram|chart|\bicon\b|orthographic|\blocation\b|topograph|administ|blank|outline|gpx|wikimedia|spreadsheet|\bsignature\b)/i;

async function fetchImages(query, max = 6) {
  if (!query) return [];
  const params = new URLSearchParams({
    action: "query", format: "json", origin: "*",
    generator: "search", gsrsearch: query, gsrnamespace: "6", gsrlimit: "40",
    prop: "imageinfo", iiprop: "url|mime|size", iiurlwidth: "1000",
  });
  let data;
  try {
    const res = await fetch("https://commons.wikimedia.org/w/api.php?" + params.toString());
    data = await res.json();
  } catch (err) { return []; }
  const pages = (data.query && data.query.pages) || {};
  const ordered = Object.values(pages).sort(
    (a, b) => (a.index == null ? 9999 : a.index) - (b.index == null ? 9999 : b.index)
  );

  const candidates = [];
  ordered.forEach((page, i) => {
    const info = (page.imageinfo && page.imageinfo[0]) || {};
    const mime = info.mime || "";
    if (!mime.startsWith("image/") || mime === "image/svg+xml") return;
    const thumb = info.thumburl || info.url;
    if (!thumb) return;
    const title = page.title || "";
    if (JUNK_IMAGE.test(title)) return;
    const w = info.width || 0, h = info.height || 0;
    if (w && w < 500) return;                         // skip tiny / thumbnail-only
    const area = w && h ? w * h : 500 * 500;
    const ratio = w && h ? Math.min(w, h) / Math.max(w, h) : 0.6; // 1 = square, →0 = sliver
    // favour big, well-proportioned, still-relevant images ("most intriguing")
    const score = Math.log(area) + ratio * 1.4 - i * 0.04;
    const caption = title.split(":").slice(1).join(":").replace(/\.[^.]+$/, "").replace(/_/g, " ").trim();
    candidates.push({ thumb, full: info.url || thumb, caption, score });
  });

  candidates.sort((a, b) => b.score - a.score);
  return candidates.slice(0, max).map(({ thumb, full, caption }) => ({ thumb, full, caption }));
}

function coverHtml(img) {
  const caption = esc(img.caption || "");
  return (
    '<figure class="cover" data-full="' + esc(img.full || img.thumb) + '" data-caption="' + caption + '">' +
      '<img loading="lazy" src="' + esc(img.thumb) + '" alt="' + caption + '" />' +
      "<figcaption>" + caption + "</figcaption>" +
    "</figure>"
  );
}

function applyCoverflow(album) {
  const rect = album.getBoundingClientRect();
  const center = rect.left + rect.width / 2;
  album.querySelectorAll(".cover").forEach((cover) => {
    const cr = cover.getBoundingClientRect();
    const coverCenter = cr.left + cr.width / 2;
    const d = (coverCenter - center) / (rect.width / 2);
    const k = Math.max(-1.4, Math.min(1.4, d));
    const rot = -k * 38;
    const scale = 1 - Math.min(Math.abs(k), 1) * 0.32;
    const tz = -Math.abs(k) * 120;
    cover.style.transform = "translateZ(" + tz + "px) rotateY(" + rot + "deg) scale(" + scale + ")";
    cover.style.zIndex = String(1000 - Math.round(Math.abs(k) * 1000));
    cover.style.opacity = String(1 - Math.min(Math.abs(k), 1) * 0.28);
  });
}

/* ====================== LIGHTBOX + TOAST ====================== */

function openLightbox(src, caption) {
  lightboxImg.src = src; lightboxImg.alt = caption || "";
  lightboxCaption.textContent = caption || ""; lightbox.hidden = false;
}
function closeLightbox() { lightbox.hidden = true; lightboxImg.src = ""; }
lightboxClose.addEventListener("click", closeLightbox);
lightbox.addEventListener("click", (e) => { if (e.target === lightbox) closeLightbox(); });

let toastTimer = null;
function toast(message) {
  toastEl.textContent = message;
  toastEl.hidden = false;
  void toastEl.offsetWidth;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.remove("show");
    setTimeout(() => { toastEl.hidden = true; }, 300);
  }, 3600);
}

/* ====================== SOUND (Web Audio — no files needed) ====================== */

const Sound = (() => {
  let ctx = null, master = null, ambient = null, muted = false;

  function ensure() {
    if (ctx) return ctx;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = 0.5;     // soft overall
      master.connect(ctx.destination);
    } catch (e) { ctx = null; }
    return ctx;
  }
  function resume() { if (ctx && ctx.state === "suspended") ctx.resume(); }
  function unlock() { ensure(); resume(); }
  function now() { return ctx.currentTime; }

  // Plucked string (oud / qanun) via Karplus-Strong synthesis — warm, soft.
  function pluck(freq, start, gain, dur, decay) {
    dur = dur || 1.7; decay = decay == null ? 0.996 : decay;
    const sr = ctx.sampleRate;
    const N = Math.max(2, Math.floor(sr / freq));
    const total = Math.floor(sr * dur);
    const ab = ctx.createBuffer(1, total, sr);
    const out = ab.getChannelData(0);
    const buf = new Float32Array(N);
    for (let i = 0; i < N; i++) buf[i] = Math.random() * 2 - 1;
    let idx = 0;
    for (let i = 0; i < total; i++) {
      const cur = buf[idx], nxt = buf[(idx + 1) % N];
      const v = (cur + nxt) * 0.5 * decay;
      out[i] = cur; buf[idx] = v; idx = (idx + 1) % N;
    }
    const fade = Math.floor(sr * 0.2);
    for (let i = 0; i < fade; i++) out[total - 1 - i] *= i / fade;
    const src = ctx.createBufferSource(); src.buffer = ab;
    const lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 2600;
    const g = ctx.createGain(); g.gain.value = gain;
    src.connect(lp); lp.connect(g); g.connect(master);
    src.start(start);
  }

  // Ney (reed flute) — soft breathy sustained tone with gentle vibrato.
  function ney(freq, start, dur, gain) {
    const o = ctx.createOscillator(); o.type = "sine"; o.frequency.value = freq;
    const vib = ctx.createOscillator(); vib.type = "sine"; vib.frequency.value = 5;
    const vibg = ctx.createGain(); vibg.gain.value = freq * 0.008;
    vib.connect(vibg); vibg.connect(o.frequency); vib.start(start); vib.stop(start + dur + 0.1);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, start);
    g.gain.exponentialRampToValueAtTime(gain, start + dur * 0.35);
    g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
    o.connect(g); g.connect(master);
    o.start(start); o.stop(start + dur + 0.1);
  }

  // Hijaz maqam on D — the unmistakable "Arabic" colour.
  const HIJAZ = [293.66, 311.13, 369.99, 392.0, 440.0, 466.16, 587.33];

  function portal() {
    if (muted || !ensure()) return; resume();
    const t = now();
    [HIJAZ[0], HIJAZ[2], HIJAZ[4], HIJAZ[6]].forEach((f, i) => pluck(f, t + i * 0.2, 0.16, 1.9, 0.997));
    ney(HIJAZ[0], t + 0.1, 2.6, 0.05);   // soft reed swell underneath
  }
  function chime() {
    if (muted || !ensure()) return; resume();
    pluck(HIJAZ[4], now(), 0.12, 1.3, 0.996);
  }
  function startAmbient() {
    if (muted || ambient || !ensure()) return; resume();
    ambient = ctx.createGain(); ambient.gain.value = 0; ambient.connect(master);
    const a = ctx.createOscillator(); a.type = "sine"; a.frequency.value = 146.83;     // D3
    const b = ctx.createOscillator(); b.type = "sine"; b.frequency.value = 220.0;       // A3 (fifth)
    const c = ctx.createOscillator(); c.type = "triangle"; c.frequency.value = 73.42;   // D2 drone
    [a, b, c].forEach((o) => o.connect(ambient));
    a.start(); b.start(); c.start();
    ambient.gain.linearRampToValueAtTime(0.03, now() + 3);
    ambient._osc = [a, b, c];
  }
  function stopAmbient() {
    if (!ambient) return;
    const a = ambient; ambient = null;
    try {
      a.gain.cancelScheduledValues(now());
      a.gain.linearRampToValueAtTime(0.0001, now() + 1.2);
      a._osc.forEach((o) => o.stop(now() + 1.4));
    } catch (e) {}
  }
  function setMuted(m) {
    muted = m;
    if (master) master.gain.value = m ? 0 : 0.5;
    if (m) stopAmbient();
  }
  return { unlock, portal, chime, startAmbient, stopAmbient, setMuted, isMuted: () => muted };
})();

// Browsers only allow audio after a user gesture — unlock on the first one.
window.addEventListener("pointerdown", () => Sound.unlock(), { once: true });
window.addEventListener("keydown", () => Sound.unlock(), { once: true });

const soundBtn = document.getElementById("sound-btn");
soundBtn.addEventListener("click", () => {
  const m = !Sound.isMuted();
  Sound.setMuted(m);
  soundBtn.textContent = m ? "🔇" : "🔊";
  if (!m && !journey.hidden) Sound.startAmbient();
});

/* ====================== HELPERS ====================== */

function wait(ms) { return new Promise((r) => setTimeout(r, ms)); }

// Rough centroid of a country polygon, for aiming the globe camera.
function centroid(feat) {
  try {
    const geom = feat.geometry;
    const polys = geom.type === "Polygon" ? [geom.coordinates] : geom.coordinates;
    let lng = 0, lat = 0, n = 0;
    polys.forEach((poly) => poly[0].forEach((pt) => { lng += pt[0]; lat += pt[1]; n++; }));
    return n ? { lat: lat / n, lng: lng / n } : null;
  } catch (e) { return null; }
}

function toRoman(n) {
  const map = [[10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]];
  let out = "";
  for (const [value, sym] of map) { while (n >= value) { out += sym; n -= value; } }
  return out;
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, (ch) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch])
  );
}

/* ====================== START ====================== */

initGlobe();
