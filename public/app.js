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

const dossier = document.getElementById("dossier");
const dossierExit = document.getElementById("dossier-exit");
const dossierBegin = document.getElementById("dossier-begin");
const dossierFlag = document.getElementById("dossier-flag");
const dossierName = document.getElementById("dossier-name");
const dossierRegion = document.getElementById("dossier-region");
const dossierOverview = document.getElementById("dossier-overview");
const dossierGallery = document.getElementById("dossier-gallery");
const dossierFlagMeaning = document.getElementById("dossier-flagmeaning");
const dossierFacts = document.getElementById("dossier-facts");
const dossierTabs = document.getElementById("dossier-tabs");
const dossierTabbody = document.getElementById("dossier-tabbody");
const dossierFunfacts = document.getElementById("dossier-funfacts");
const dossierHeroBg = document.getElementById("dossier-hero-bg");
const galleryTitle = document.getElementById("dossier-gallery-title");

const story = document.getElementById("story");
const storyRail = document.getElementById("story-rail");
const storyExit = document.getElementById("story-exit");

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

/* Recognizable landmark silhouettes (SVG, viewBox 0 0 100 44, baseline y=44).
   Rendered as a dark silhouette at the foot of the portal scene. */
const LANDMARKS = {
  pyramids:  "<polygon points='0,44 16,15 32,44'/><polygon points='27,44 50,5 73,44'/><polygon points='63,44 80,18 98,44'/>",
  ziggurat:  "<path d='M30 44 V38 H36 V32 H42 V26 H46 V20 H54 V26 H58 V32 H64 V38 H70 V44 Z'/>",
  eiffel:    "<path d='M50 2 L48.6 9 L51.4 9 Z'/><path d='M47.5 9 L52.5 9 L51 18 L49 18 Z'/><path d='M45 18 L55 18 L57 29 L43 29 Z'/><rect x='42' y='28' width='16' height='2'/><path d='M43 30 L37 44 L42.5 44 L49 33 L51 33 L57.5 44 L63 44 L57 30 Z'/>",
  taj:       "<rect x='34' y='30' width='32' height='14'/><path d='M50 11 Q39 19 41 30 L59 30 Q61 19 50 11 Z'/><rect x='49' y='5' width='2' height='7'/><rect x='27' y='18' width='3' height='26'/><path d='M28.5 14 Q26 17 27 18 L30 18 Q31 17 28.5 14 Z'/><rect x='70' y='18' width='3' height='26'/><path d='M71.5 14 Q69 17 70 18 L73 18 Q74 17 71.5 14 Z'/>",
  bigben:    "<rect x='44' y='15' width='12' height='29'/><polygon points='44,15 50,6 56,15'/><rect x='48.5' y='3' width='3' height='3'/><circle cx='50' cy='23' r='3'/>",
  parthenon: "<polygon points='28,16 50,7 72,16'/><rect x='28' y='16' width='44' height='3'/><rect x='30' y='19' width='4' height='23'/><rect x='38' y='19' width='4' height='23'/><rect x='46' y='19' width='4' height='23'/><rect x='54' y='19' width='4' height='23'/><rect x='62' y='19' width='4' height='23'/><rect x='28' y='42' width='44' height='2'/>",
  colosseum: "<path d='M18 44 V27 Q50 17 82 27 V44 Z M26 31 h6 v8 h-6 Z M38 29 h6 v9 h-6 Z M50 28 h6 v9 h-6 Z M62 29 h6 v9 h-6 Z M74 31 h6 v8 h-6 Z'/>",
  fuji:      "<polygon points='16,44 40,15 60,15 84,44'/><rect x='24' y='31' width='2' height='13'/><rect x='34' y='31' width='2' height='13'/><rect x='21' y='29' width='18' height='2'/><rect x='22.5' y='32' width='15' height='1.4'/>",
  greatwall: "<path d='M0 44 V33 L18 31 V27 L23 27 V31 L46 28 V24 L51 24 V28 L74 26 V22 L79 22 V26 L100 25 V44 Z'/>",
  stbasil:   "<rect x='44' y='22' width='12' height='22'/><path d='M50 6 Q42 16 44 22 L56 22 Q58 16 50 6 Z'/><rect x='49' y='2' width='2' height='4'/><rect x='30' y='28' width='9' height='16'/><path d='M34.5 16 Q28 24 30 28 L39 28 Q41 24 34.5 16 Z'/><rect x='61' y='28' width='9' height='16'/><path d='M65.5 16 Q59 24 61 28 L70 28 Q72 24 65.5 16 Z'/>",
  redeemer:  "<polygon points='22,44 50,27 78,44'/><rect x='49' y='9' width='2' height='19'/><rect x='40' y='14' width='20' height='2'/><circle cx='50' cy='8' r='1.6'/>",
  opera:     "<path d='M18 44 Q24 25 38 44 Z'/><path d='M32 44 Q41 20 55 44 Z'/><path d='M49 44 Q57 27 69 44 Z'/><path d='M63 44 Q71 31 82 44 Z'/>",
  petra:     "<polygon points='34,14 50,6 66,14'/><rect x='34' y='14' width='32' height='2'/><rect x='36' y='16' width='3' height='28'/><rect x='44' y='16' width='3' height='28'/><rect x='53' y='16' width='3' height='28'/><rect x='61' y='16' width='3' height='28'/><path d='M47 30 V22 Q50 18 53 22 V30 Z'/>",
  angkor:    "<path d='M50 6 Q46 16 48 26 L52 26 Q54 16 50 6 Z'/><rect x='47' y='26' width='6' height='18'/><path d='M34 13 Q31 20 33 28 L37 28 Q39 20 36 13 Z'/><rect x='33' y='28' width='4' height='16'/><path d='M66 13 Q64 20 67 28 L71 28 Q69 20 66 13 Z'/><rect x='64' y='28' width='4' height='16'/><path d='M22 20 Q20 26 22 31 L26 31 Q28 26 26 20 Z'/><rect x='22' y='31' width='4' height='13'/><path d='M78 20 Q76 26 78 31 L82 31 Q84 26 82 20 Z'/><rect x='78' y='31' width='4' height='13'/>",
  burj:      "<path d='M50 3 L47 22 L44 44 L56 44 L53 22 Z'/><rect x='30' y='28' width='8' height='16'/><rect x='40' y='34' width='5' height='10'/><rect x='60' y='32' width='6' height='12'/><rect x='70' y='26' width='7' height='18'/>",
  skyline:   "<rect x='4' y='28' width='9' height='16'/><rect x='15' y='22' width='8' height='22'/><rect x='25' y='32' width='7' height='12'/><rect x='34' y='18' width='9' height='26'/><rect x='45' y='26' width='8' height='18'/><rect x='55' y='14' width='9' height='30'/><rect x='66' y='24' width='7' height='20'/><rect x='75' y='30' width='8' height='14'/><rect x='85' y='20' width='9' height='24'/>",
  // sub-region fallbacks — so every country gets a fitting silhouette
  mosque:    "<rect x='34' y='30' width='32' height='14'/><path d='M50 12 Q38 20 40 30 L60 30 Q62 20 50 12 Z'/><rect x='49' y='6' width='2' height='6'/><rect x='26' y='16' width='3' height='28'/><path d='M27.5 12 Q25 15 26 16 L29 16 Q30 15 27.5 12 Z'/><rect x='71' y='16' width='3' height='28'/><path d='M72.5 12 Q70 15 71 16 L74 16 Q75 15 72.5 12 Z'/>",
  pagoda:    "<rect x='47' y='12' width='6' height='32'/><polygon points='34,18 50,12 66,18 60,20 50,16 40,20'/><polygon points='31,28 50,22 69,28 62,30 50,26 38,30'/><polygon points='28,38 50,32 72,38 64,40 50,36 36,40'/><rect x='49' y='8' width='2' height='4'/>",
  temple:    "<path d='M38 44 L40 22 L44 22 L45 14 L55 14 L56 22 L60 22 L62 44 Z'/><polygon points='48,14 50,9 52,14'/><rect x='42' y='20' width='16' height='2'/><rect x='40' y='28' width='20' height='2'/><rect x='39' y='36' width='22' height='2'/>",
  acacia:    "<rect x='48' y='28' width='4' height='16'/><path d='M30 26 Q50 15 70 26 Q70 30 50 29 Q30 30 30 26 Z'/><rect x='75' y='34' width='2' height='10'/><path d='M67 32 Q76 25 85 32 Q85 35 76 34 Q67 35 67 32 Z'/>",
  cathedral: "<rect x='38' y='20' width='24' height='24'/><rect x='40' y='10' width='6' height='34'/><polygon points='40,10 43,2 46,10'/><rect x='54' y='10' width='6' height='34'/><polygon points='54,10 57,2 60,10'/><circle cx='50' cy='22' r='2.5'/>",
  castle:    "<path d='M30 44 V24 H32 V20 H35 V24 H38 V20 H41 V24 H59 V20 H62 V24 H65 V20 H68 V24 H70 V44 Z'/><path d='M26 44 V16 H28 V13 H30 V16 H32 V13 H34 V16 H36 V44 Z'/><path d='M64 44 V16 H66 V13 H68 V16 H70 V13 H72 V16 H74 V44 Z'/><path d='M46 44 V32 Q50 28 54 32 V44 Z'/>",
  palm:      "<path d='M0 44 Q50 40 100 44 Z'/><polygon points='39,44 41,44 43,24 41,24'/><polygon points='42,24 30,18 44,22'/><polygon points='42,24 54,18 42,22'/><polygon points='42,23 34,14 44,21'/><polygon points='42,23 50,14 42,21'/><polygon points='59,44 61,44 59,26 57,26'/><polygon points='58,26 46,21 60,24'/><polygon points='58,26 70,21 58,24'/>",
  mountains: "<polygon points='0,44 20,16 34,32 50,8 66,30 82,18 100,44'/>",
  cedars:    "<rect x='48' y='32' width='4' height='12'/><polygon points='50,8 38,22 62,22'/><polygon points='50,16 34,30 66,30'/><polygon points='50,24 30,38 70,38'/>",
};

/* Country → its iconic landmark (expanded by the loop toward full coverage). */
const LANDMARK_BY_COUNTRY = {
  "Egypt": "pyramids", "Sudan": "pyramids", "Mexico": "pyramids",
  "Iraq": "ziggurat", "Jordan": "petra", "Greece": "parthenon", "Italy": "colosseum",
  "France": "eiffel", "United Kingdom": "bigben", "India": "taj", "Japan": "fuji",
  "China": "greatwall", "Russia": "stbasil", "Brazil": "redeemer", "Australia": "opera",
  "Cambodia": "angkor", "United Arab Emirates": "burj", "United States of America": "skyline",
  "Lebanon": "cedars",
};

// Every UN sub-region gets a fitting landmark, so NO country is left without one.
const LANDMARK_BY_SUBREGION = {
  "Northern Africa": "mosque", "Eastern Africa": "acacia", "Middle Africa": "acacia",
  "Western Africa": "acacia", "Southern Africa": "acacia",
  "Northern America": "skyline", "Central America": "pyramids", "Caribbean": "palm",
  "South America": "mountains",
  "Northern Europe": "cathedral", "Western Europe": "cathedral", "Southern Europe": "parthenon",
  "Eastern Europe": "castle",
  "Western Asia": "mosque", "Central Asia": "mosque", "Southern Asia": "temple",
  "Eastern Asia": "pagoda", "South-Eastern Asia": "temple",
  "Australia and New Zealand": "skyline", "Melanesia": "palm",
  "Antarctica": "mountains", "Seven seas (open ocean)": "palm",
};

const PALETTE_BY_CONTINENT = {
  "Africa": "sand", "Asia": "clay", "Europe": "dusk",
  "North America": "gulf", "South America": "cedar", "Oceania": "gulf",
};

function themeFor(country) {
  const t = COUNTRY_THEME[country] || {};
  const palette = t.palette || PALETTE_BY_CONTINENT[lastHoverContinent] || "dusk";
  const p = PALETTES[palette] || PALETTES.dusk;
  // bespoke icon → sub-region icon → safe default. Always returns a landmark.
  const landmark = LANDMARK_BY_COUNTRY[country] || LANDMARK_BY_SUBREGION[lastHoverSubregion] || "mountains";
  return {
    sky: p.sky, sun: p.sun, accent: p.accent,
    motif: t.motif || "mountains",
    label: t.label || ("Into " + country),
    landmark: landmark,
  };
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
let lastHoverSubregion = null;
let lastHoverContinent = null;
let dwellCountry = null;
let dwellTimer = null;

/* ====================== GLOBE ====================== */

function initGlobe() {
  const el = document.getElementById("globe");
  if (typeof Globe === "undefined" || !el) return showFallback();

  try {
    world = Globe()(el)
      .backgroundColor("#3b34dd")     // Radio-Garden blue backdrop (no starfield)
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
        if (pt) {
          lastHoverLatLng = { lat: pt.lat, lng: pt.lng };
          lastHoverSubregion = pt.country === "Bahrain" ? "Western Asia" : "Eastern Africa";
          lastHoverContinent = pt.country === "Bahrain" ? "Asia" : "Africa";
        }
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
          if (feat) {
            lastHoverLatLng = centroid(feat);
            lastHoverSubregion = feat.properties.SUBREGION || null;
            lastHoverContinent = feat.properties.CONTINENT || null;
          }
          refreshPolygonStyles();
          recomputeHover();
        })
        // tap/click a country to enter — essential on phones, which can't hover
        .onPolygonClick((feat) => {
          if (!feat || busy) return;
          lastHoverLatLng = centroid(feat);
          lastHoverSubregion = feat.properties.SUBREGION || null;
          lastHoverContinent = feat.properties.CONTINENT || null;
          enterCountry(feat.properties.ADMIN);
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

// When WebGL is unavailable (e.g. the in-app preview pane), we still want the
// Radio-Garden experience: a real, draggable, spinning globe you can hover and
// click. This renders the actual country shapes with a 2D-canvas orthographic
// projection — no WebGL needed.
function showFallback() {
  if (!globeFallback) return;
  globeFallback.hidden = false;
  initGlobe2D();
}

function initGlobe2D() {
  globeFallback.innerHTML = '<canvas class="globe-canvas" id="globe-canvas"></canvas>';
  const canvas = document.getElementById("globe-canvas");
  const ctx = canvas.getContext("2d");
  const DEG = Math.PI / 180;

  const s = {
    rotLng: 35, rotLat: 20,           // longitude/latitude at the centre of the disc
    dragging: false, lastX: 0, lastY: 0, moved: 0,
    autoRotate: true, hoverFeat: null,
    features: [], cx: 0, cy: 0, R: 0, R0: 0, zoom: 1, vel: 0, lastT: 0, dwell: null,
  };

  // Earth texture, sampled per-pixel to paint a real rotating globe (no WebGL).
  let tex = null;                                   // { data, w, h }
  let buf = null, bufCtx = null, bufImg = null, bufD = 0;   // low-res sphere buffer
  (function loadTexture() {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const tw = 2048, th = 1024;                   // higher-res texture → crisper continents
      const oc = document.createElement("canvas"); oc.width = tw; oc.height = th;
      const octx = oc.getContext("2d");
      octx.drawImage(img, 0, 0, tw, th);
      try { tex = { data: octx.getImageData(0, 0, tw, th).data, w: tw, h: th }; s.bufKey = null; }
      catch (e) { tex = null; }                     // tainted → plain-shaded fallback
    };
    img.src = "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg";
  })();

  function makeBuffer(D) {
    bufD = D;
    buf = document.createElement("canvas"); buf.width = bufD; buf.height = bufD;
    bufCtx = buf.getContext("2d");
    bufImg = bufCtx.createImageData(bufD, bufD);
    s.bufKey = null;                                            // force a fresh sphere paint
  }
  function setSizes() {
    // crisp when still, lighter while moving → smooth 60fps spin without losing sharpness at rest
    s.hiD = Math.max(80, Math.min(Math.round(2 * s.R), 760));
    s.loD = Math.max(80, Math.min(Math.round(2 * s.R), 460));
  }
  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth, h = window.innerHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    canvas.style.width = w + "px"; canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    s.cx = w / 2; s.cy = h / 2; s.R0 = Math.min(w, h) * 0.34; s.R = s.R0 * s.zoom;
    setSizes(); makeBuffer(s.hiD);
  }
  function applyZoom() { s.R = s.R0 * s.zoom; setSizes(); makeBuffer(bufD > (s.loD + s.hiD) / 2 ? s.hiD : s.loD); }
  resize();
  let resizeT = null;
  window.addEventListener("resize", () => { clearTimeout(resizeT); resizeT = setTimeout(resize, 120); });
  // scroll to zoom (matches the hint; the 3D globe already zooms on its own)
  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    s.zoom = Math.max(0.8, Math.min(2.2, s.zoom * (e.deltaY < 0 ? 1.12 : 0.89)));
    applyZoom();
  }, { passive: false });

  fetch(COUNTRIES_GEOJSON)
    .then((r) => r.json())
    .then((gj) => {
      s.features = (gj.features || []).map((f) => {
        const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
        let m0 = 180, m1 = 90, m2 = -180, m3 = -90;   // bbox: minLng,minLat,maxLng,maxLat
        for (const poly of polys) for (const ring of poly) for (const pt of ring) {
          if (pt[0] < m0) m0 = pt[0]; if (pt[0] > m2) m2 = pt[0];
          if (pt[1] < m1) m1 = pt[1]; if (pt[1] > m3) m3 = pt[1];
        }
        return {
          admin: f.properties.ADMIN, sub: f.properties.SUBREGION || null,
          cont: f.properties.CONTINENT || null, polys: polys, feat: f, bbox: [m0, m1, m2, m3],
        };
      });
    })
    .catch(() => { s.dead = true; showChips(); });

  // --- orthographic projection ---
  function project(lng, lat) {
    const l = (lng - s.rotLng) * DEG, p = lat * DEG, p0 = s.rotLat * DEG;
    const cosc = Math.sin(p0) * Math.sin(p) + Math.cos(p0) * Math.cos(p) * Math.cos(l);
    return {
      x: s.cx + s.R * (Math.cos(p) * Math.sin(l)),
      y: s.cy - s.R * (Math.cos(p0) * Math.sin(p) - Math.sin(p0) * Math.cos(p) * Math.cos(l)),
      vis: cosc >= 0,
    };
  }
  function unproject(px, py) {
    const x = (px - s.cx) / s.R, y = -(py - s.cy) / s.R;
    const rho = Math.sqrt(x * x + y * y);
    if (rho > 1) return null;
    const c = Math.asin(Math.min(1, rho)), p0 = s.rotLat * DEG;
    if (rho < 1e-9) return { lng: s.rotLng, lat: s.rotLat };
    const lat = Math.asin(Math.cos(c) * Math.sin(p0) + (y * Math.sin(c) * Math.cos(p0)) / rho) / DEG;
    const lng = s.rotLng + Math.atan2(x * Math.sin(c), rho * Math.cos(c) * Math.cos(p0) - y * Math.sin(c) * Math.sin(p0)) / DEG;
    return { lng, lat };
  }
  function pointInPoly(lng, lat, poly) {
    let inside = false;
    for (const ring of poly) {
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
        if ((yi > lat) !== (yj > lat) && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
      }
    }
    return inside;
  }
  function featureAt(lng, lat) {
    for (const f of s.features) {
      const b = f.bbox;
      if (b && (lng < b[0] || lng > b[2] || lat < b[1] || lat > b[3])) continue;  // fast reject
      for (const poly of f.polys) if (pointInPoly(lng, lat, poly)) return f;
    }
    return null;
  }

  // --- drawing (Radio-Garden look: real textured Earth on bright blue) ---
  function renderSphere() {
    // soft atmosphere halo
    const glow = ctx.createRadialGradient(s.cx, s.cy, s.R * 0.94, s.cx, s.cy, s.R * 1.14);
    glow.addColorStop(0, "rgba(170,195,255,0.45)");
    glow.addColorStop(1, "rgba(170,195,255,0)");
    ctx.fillStyle = glow;
    ctx.beginPath(); ctx.arc(s.cx, s.cy, s.R * 1.14, 0, 6.2832); ctx.fill();

    if (!tex) {                                  // texture not ready yet → plain sphere
      const oc = ctx.createRadialGradient(s.cx - s.R * 0.3, s.cy - s.R * 0.3, s.R * 0.1, s.cx, s.cy, s.R);
      oc.addColorStop(0, "#1b3e63"); oc.addColorStop(1, "#08203a");
      ctx.beginPath(); ctx.arc(s.cx, s.cy, s.R, 0, 6.2832); ctx.fillStyle = oc; ctx.fill();
      return;
    }
    // Only repaint the per-pixel sphere when the view actually changed (huge win
    // while paused on hover); otherwise just blit the cached buffer.
    const key = (s.rotLng | 0) + "_" + (s.rotLat * 4 | 0) + "_" + bufD + "_" + ((s.rotLng * 4) | 0);
    if (key !== s.bufKey) {
      s.bufKey = key;
      const D = bufD, half = D / 2, out = bufImg.data;
      const td = tex.data, tw = tex.w, th = tex.h;
      const p0 = s.rotLat * DEG, sinP0 = Math.sin(p0), cosP0 = Math.cos(p0), rot = s.rotLng;
      let o = 0;
      for (let j = 0; j < D; j++) {
        const ny = (j - half) / half, yW = -ny, ny2 = ny * ny;
        for (let i = 0; i < D; i++, o += 4) {
          const nx = (i - half) / half;
          const rho2 = nx * nx + ny2;
          if (rho2 > 1) { out[o + 3] = 0; continue; }
          const z = Math.sqrt(1 - rho2);
          let v1 = z * sinP0 + yW * cosP0;
          v1 = v1 < -1 ? -1 : v1 > 1 ? 1 : v1;
          const lat = Math.asin(v1) / DEG;
          let lng = rot + Math.atan2(nx, z * cosP0 - yW * sinP0) / DEG;
          lng = ((lng + 180) % 360 + 360) % 360;
          let tu = (lng / 360 * tw) | 0; if (tu >= tw) tu = tw - 1;
          let tv = ((90 - lat) / 180 * th) | 0; if (tv < 0) tv = 0; else if (tv >= th) tv = th - 1;
          const ti = (tv * tw + tu) << 2;
          const shade = 0.5 + 0.5 * z;             // gentle limb darkening
          out[o] = td[ti] * shade;
          out[o + 1] = td[ti + 1] * shade;
          out[o + 2] = td[ti + 2] * shade;
          out[o + 3] = rho2 > 0.98 ? (1 - Math.sqrt(rho2)) / (1 - Math.sqrt(0.98)) * 255 : 255;
        }
      }
      bufCtx.putImageData(bufImg, 0, 0);
    }
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(buf, s.cx - s.R, s.cy - s.R, s.R * 2, s.R * 2);
  }

  // highlight the hovered country (glowing fill + outline) on the textured globe
  function drawHighlight() {
    const f = s.hoverFeat;
    if (!f) return;
    ctx.save();
    ctx.beginPath(); ctx.arc(s.cx, s.cy, s.R, 0, 6.2832); ctx.clip();   // stay on the near hemisphere
    ctx.beginPath();
    for (const poly of f.polys) for (const ring of poly) {
      let on = false;
      for (const pt of ring) {
        const p = project(pt[0], pt[1]);
        if (!p.vis) { on = false; continue; }
        if (!on) { ctx.moveTo(p.x, p.y); on = true; } else ctx.lineTo(p.x, p.y);
      }
    }
    ctx.fillStyle = "rgba(255,236,170,0.32)";
    ctx.fill("evenodd");
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(255,246,214,0.96)";
    ctx.stroke();
    ctx.restore();
  }
  function render() {
    if (s.dead) return;                       // canvas was torn down (chip fallback) — stop ticking
    if (globeView.style.display !== "none") {
      // resolve at most one hover hit-test per frame (cheaper than per pointermove)
      if (s.pendingHover && !s.dragging) {
        const g = unproject(s.pendingHover.x, s.pendingHover.y);
        setHover(g ? featureAt(g.lng, g.lat) : null, g);
        s.pendingHover = null;
      }
      ctx.fillStyle = "#3b34dd"; ctx.fillRect(0, 0, window.innerWidth, window.innerHeight);   // Radio-Garden blue
      const now = performance.now();
      const dt = s.lastT ? Math.min(60, now - s.lastT) : 16; s.lastT = now;
      const moving = s.dragging || Math.abs(s.vel) > 0.0008 || (s.autoRotate && !s.hoverFeat && !busy);
      if (!s.dragging && !s.hoverFeat && !busy) {
        if (Math.abs(s.vel) > 0.0006) { s.rotLng += s.vel * dt; s.vel *= Math.pow(0.94, dt / 16); }  // fling momentum
        else if (s.autoRotate) s.rotLng += 0.006 * dt;                                                 // gentle, fps-independent spin
      }
      // light buffer while moving (smooth), crisp buffer once it settles
      const wantD = moving ? s.loD : s.hiD;
      if (wantD !== bufD) makeBuffer(wantD);
      renderSphere();
      drawHighlight();
    }
    requestAnimationFrame(render);
  }
  render();

  // --- interaction ---
  function setHoverGlobals(f, geo) {
    lastHoverLatLng = geo ? { lat: geo.lat, lng: geo.lng } : centroid(f.feat);
    lastHoverSubregion = f.sub; lastHoverContinent = f.cont;
  }
  function setHover(f, geo) {
    if (s.hoverFeat === f) return;
    s.hoverFeat = f;
    clearTimeout(s.dwell);
    canvas.style.cursor = f ? "pointer" : "grab";
    if (f) {
      s.vel = 0;                 // stop any fling so the country stays put under the cursor
      setHoverGlobals(f, geo);
      s.dwell = setTimeout(() => { if (s.hoverFeat === f && !busy) enterCountry(f.admin); }, 2000);
    }
  }
  canvas.addEventListener("pointerdown", (e) => {
    s.dragging = true; s.moved = 0; s.vel = 0; s.moveT = performance.now();
    s.lastX = e.clientX; s.lastY = e.clientY;
    clearTimeout(s.dwell); s.hoverFeat = null;
    try { canvas.setPointerCapture(e.pointerId); } catch (_) {}
    canvas.style.cursor = "grabbing";
  });
  canvas.addEventListener("pointermove", (e) => {
    if (s.dragging) {
      const now = performance.now(), mdt = Math.max(1, now - (s.moveT || now)); s.moveT = now;
      const dx = e.clientX - s.lastX, dy = e.clientY - s.lastY;
      s.moved += Math.abs(dx) + Math.abs(dy);
      const dLng = -dx * 0.25;
      s.rotLng += dLng; s.rotLat += dy * 0.25;
      s.rotLat = Math.max(-82, Math.min(82, s.rotLat));
      s.vel = dLng / mdt;                       // deg/ms → fling momentum on release
      s.lastX = e.clientX; s.lastY = e.clientY;
    } else {
      s.pendingHover = { x: e.clientX, y: e.clientY };   // resolved once per frame in render()
    }
  });
  canvas.addEventListener("pointerup", (e) => {
    s.dragging = false; canvas.style.cursor = "grab";
    if (s.moved < 6) {
      const geo = unproject(e.clientX, e.clientY);
      const f = geo ? featureAt(geo.lng, geo.lat) : null;
      if (f && !busy) { setHoverGlobals(f, geo); enterCountry(f.admin); }
    }
  });
  // If a drag is interrupted (pointercancel / lost capture / pointer leaves),
  // always release the drag so the globe can never get stuck frozen.
  function endDrag() { s.dragging = false; canvas.style.cursor = "grab"; }
  canvas.addEventListener("pointercancel", endDrag);
  canvas.addEventListener("lostpointercapture", endDrag);
  canvas.addEventListener("pointerleave", () => { endDrag(); s.pendingHover = null; setHover(null); });
}

// Last-resort list, only if the country shapes can't be fetched at all.
function showChips() {
  if (!globeFallback) return;
  const popular = [
    "Egypt", "Greece", "Italy", "France", "Spain", "United Kingdom", "Germany",
    "Turkey", "Iraq", "Iran", "Saudi Arabia", "Morocco", "India", "China",
    "Japan", "Mexico", "Peru", "United States of America", "Russia", "Ethiopia",
  ];
  globeFallback.innerHTML =
    '<div class="fallback-inner"><p>Choose a civilization to explore</p><div class="fallback-list">' +
    popular.map((c) => '<button class="chip" data-country="' + esc(c) + '">' + esc(c) + "</button>").join("") +
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
    }, 2000);   // launch the portal after 2s of resting on a country
  }
}

/* ====================== PORTAL ====================== */

function playPortal(country) {
  const theme = themeFor(country);
  portalScene.style.background = theme.sky;
  portal.style.setProperty("--accent", theme.accent);
  portal.style.setProperty("--sun", theme.sun);
  const landmark = theme.landmark && LANDMARKS[theme.landmark];
  portalScene.innerHTML =
    '<div class="sun"></div>' +
    (landmark
      ? '<svg class="landmark" viewBox="0 0 100 44" preserveAspectRatio="xMidYMax meet">' + landmark + "</svg>"
      : '<div class="motif motif-' + theme.motif + '"></div>');
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
  ensureEraImages(0);   // warm the first era while the dossier is open → instant timeline
  if (data.demo) toast("Demo mode — built-in Egypt sample. Add an API key for any country.");

  // Arrive on the country dossier first; the timeline is one click away.
  globeView.style.display = "none";
  showDossier(country);
  endPortal();
}

/* ====================== COUNTRY DOSSIER ====================== */

let dossierToken = 0;
async function showDossier(country) {
  const token = ++dossierToken;   // guards against a stale fetch overwriting a newer country
  dossier.hidden = false;
  window.scrollTo(0, 0);
  dossierName.textContent = country;
  dossierRegion.textContent = "";
  dossierFlag.removeAttribute("src");
  dossierOverview.innerHTML = '<span class="dossier-loading">Compiling the dossier…</span>';
  dossierGallery.innerHTML = "";
  dossierFlagMeaning.innerHTML = "";
  dossierFacts.innerHTML = "";
  dossierTabs.innerHTML = "";
  dossierTabs._sections = null;
  dossierTabbody.innerHTML = "";
  dossierFunfacts.innerHTML = "";
  if (dossierHeroBg) dossierHeroBg.style.backgroundImage = "none";
  if (galleryTitle) galleryTitle.hidden = true;

  const [facts, profileResp] = await Promise.all([
    fetchCountryFacts(country),
    fetch("/api/profile?country=" + encodeURIComponent(country)).then((r) => r.json()).catch(() => null),
  ]);
  if (token !== dossierToken) return;   // a newer dossier opened while we were fetching
  renderDossier(country, facts, profileResp && profileResp.profile);
}

async function fetchCountryFacts(country) {
  try {
    const res = await fetch(
      "https://restcountries.com/v3.1/name/" + encodeURIComponent(country) +
      "?fields=name,flags,capital,population,area,region,subregion,languages,currencies"
    );
    if (!res.ok) return null;
    const arr = await res.json();
    if (!Array.isArray(arr) || !arr.length) return null;
    return arr.find((c) => ((c.name && c.name.common) || "").toLowerCase() === country.toLowerCase()) || arr[0];
  } catch (e) {
    return null;
  }
}

function renderDossier(country, facts, profile) {
  if (facts) {
    if (facts.flags && facts.flags.svg) dossierFlag.src = facts.flags.svg;
    dossierName.textContent = (profile && profile.officialName) || (facts.name && facts.name.common) || country;
    dossierRegion.textContent = [facts.subregion, facts.region].filter(Boolean).join(" · ");
  } else if (profile && profile.officialName) {
    dossierName.textContent = profile.officialName;
  }

  dossierOverview.textContent = (profile && profile.overview) || "";

  if (profile && profile.flagMeaning) {
    dossierFlagMeaning.innerHTML = "<b>The Flag</b>" + esc(profile.flagMeaning);
  }

  if (facts) {
    const rows = [];
    if (facts.capital && facts.capital[0]) rows.push(["Capital", facts.capital[0]]);
    if (facts.population) rows.push(["Population", facts.population.toLocaleString()]);
    if (facts.area) rows.push(["Area", Math.round(facts.area).toLocaleString() + " km²"]);
    if (facts.languages) rows.push(["Languages", Object.values(facts.languages).join(", ")]);
    if (facts.currencies) rows.push(["Currency", Object.values(facts.currencies).map((c) => c.name).join(", ")]);
    if (facts.region) rows.push(["Region", facts.region]);
    const FACT_ICON = { Capital: "🏛️", Population: "👥", Area: "📐", Languages: "🗣️", Currency: "💰", Region: "🗺️" };
    dossierFacts.innerHTML = rows
      .map(([l, v]) => '<span class="chip"><span class="chip-ico">' + (FACT_ICON[l] || "📌") + "</span><b>" + esc(l) + "</b>" + esc(v) + "</span>")
      .join("");
  }

  if (profile) {
    const sections = [
      ["Political", profile.political], ["Physical", profile.physical],
      ["Demographics", profile.demographics], ["Economy", profile.economy], ["Culture", profile.culture],
    ].filter(([, t]) => t);
    if (sections.length) {
      const TAB_ICON = { Political: "🏛️", Physical: "🏔️", Demographics: "👥", Economy: "💹", Culture: "🎭" };
      dossierTabs.innerHTML = sections
        .map(([h], i) => '<button class="tab-btn' + (i === 0 ? " active" : "") + '" data-tab="' + i + '">' + (TAB_ICON[h] ? TAB_ICON[h] + " " : "") + esc(h) + "</button>")
        .join("");
      dossierTabbody.textContent = sections[0][1];
      dossierTabs._sections = sections;
    }
    if (Array.isArray(profile.funFacts) && profile.funFacts.length) {
      dossierFunfacts.innerHTML =
        "<h3>💡 Did you know?</h3><ul>" + profile.funFacts.map((x) => "<li>" + esc(x) + "</li>").join("") + "</ul>";
    }
  } else {
    dossierTabbody.innerHTML = '<span class="dossier-loading">Profile unavailable right now (check the Gemini key).</span>';
  }

  // photo gallery — use Gemini's suggested searches (fallback to generics)
  const queries = profile && Array.isArray(profile.imageQueries) && profile.imageQueries.length
    ? profile.imageQueries
    : [country + " landmark", country + " landscape", (facts && facts.capital && facts.capital[0]) || country];
  loadGallery(queries);
}

async function loadGallery(queries) {
  const token = dossierToken;
  dossierGallery.innerHTML = '<span class="dossier-loading">Gathering photos…</span>';
  const qs = [], seenQ = new Set();
  for (const q of queries) { const c = (q || "").trim().toLowerCase(); if (c && !seenQ.has(c)) { seenQ.add(c); qs.push(q); } }
  const use = qs.slice(0, 8);
  const results = await Promise.all(use.map((q) => fetchImages(q, 4)));
  if (token !== dossierToken) return;   // dossier changed while photos loaded
  const imgs = [];
  const seen = new Set();
  use.forEach((q, k) => {
    for (const im of (results[k] || [])) {     // one distinct photo per subject (no repeats)
      const id = im.id || im.thumb;
      if (seen.has(id)) continue;
      seen.add(id); imgs.push(Object.assign({}, im, { caption: subjectCaption(q) }));
      break;
    }
  });
  if (!imgs.length) { dossierGallery.innerHTML = ""; if (galleryTitle) galleryTitle.hidden = true; return; }
  // big cinematic header image = first striking photo
  if (dossierHeroBg) dossierHeroBg.style.backgroundImage = "url('" + (imgs[0].full || imgs[0].thumb).replace(/'/g, "%27") + "')";
  if (galleryTitle) galleryTitle.hidden = false;
  dossierGallery.innerHTML = imgs.slice(0, 10)
    .map((im, i) =>
      '<figure class="gallery-photo" data-full="' + esc(im.full || im.thumb) + '" data-caption="' + esc(im.caption || "") + '">' +
        "<img " + (i === 0 ? 'fetchpriority="high"' : 'loading="lazy"') + ' decoding="async" src="' + esc(im.thumb) + '" alt="' + esc(im.caption || "") + '"/>' +
        (im.caption ? "<span>" + esc(im.caption) + "</span>" : "") +
      "</figure>")
    .join("");
  dossierGallery.querySelectorAll("img").forEach((img) => {
    const done = () => img.classList.add("loaded");
    if (img.complete) done(); else { img.addEventListener("load", done); img.addEventListener("error", done); }
  });
}

dossierTabs.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-tab]");
  if (!btn || !dossierTabs._sections) return;
  dossierTabs.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
  dossierTabbody.textContent = dossierTabs._sections[parseInt(btn.getAttribute("data-tab"), 10)][1];
});

dossier.addEventListener("click", (e) => {
  const fig = e.target.closest(".gallery-photo");
  if (fig) openLightbox(fig.getAttribute("data-full"), fig.getAttribute("data-caption"));
});

/* ====================== STORY (level 3) ====================== */

eraStage.addEventListener("click", (e) => {
  const s = e.target.closest("[data-story]");
  if (s) openStory(parseInt(s.getAttribute("data-story"), 10));
});

let storyObserver = null;
function closeStory() {
  story.hidden = true;
  if (storyObserver) { storyObserver.disconnect(); storyObserver = null; }
}
storyExit.addEventListener("click", closeStory);

// Prefetch + cache an era's legend so opening it feels instant. Dedupes via a
// shared promise on the era object; safe to call on hover and on click.
function prefetchStory(index) {
  const era = currentEras[index];
  if (!era || era._story) return Promise.resolve(era && era._story);
  if (!era._storyPromise) {
    era._storyPromise = fetch(
      "/api/story?country=" + encodeURIComponent(currentCountry) +
      "&era=" + encodeURIComponent(era.title || "") +
      "&period=" + encodeURIComponent(era.period || "")
    )
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => { era._story = (j && j.story) || null; return era._story; })
      .catch(() => { era._story = null; return null; });
  }
  return era._storyPromise;
}

async function openStory(index) {
  const era = currentEras[index];
  if (!era) return;
  story.hidden = false;
  story.scrollTop = 0;
  storyRail.innerHTML =
    '<section class="beat in"><div class="beat-scrim"></div><div class="beat-inner">' +
    '<p class="beat-text" style="opacity:1;transform:none">Summoning the legend…</p></div></section>';

  if (!era._story) {
    try { await prefetchStory(index); } catch (e) {}
  }
  const data = era._story;
  if (!data || !Array.isArray(data.beats) || !data.beats.length) {
    storyRail.innerHTML =
      '<section class="beat in"><div class="beat-scrim"></div><div class="beat-inner">' +
      '<p class="beat-text" style="opacity:1;transform:none">The legend could not be summoned. Try again.</p></div></section>';
    era._story = null; era._storyPromise = null;   // allow a clean retry next time
    return;
  }
  renderStory(data, era);
}

function renderStory(data, era) {
  storyRail.innerHTML = data.beats
    .map((b, i) =>
      '<section class="beat" data-beat="' + i + '">' +
        '<div class="beat-bg"></div><div class="beat-scrim"></div>' +
        '<div class="beat-inner">' +
          (i === 0
            ? '<p class="beat-kicker">' + esc(era.title || "") + ' · the legend</p><h2 class="beat-storytitle">' + esc(data.title || "") + "</h2>"
            : "") +
          '<p class="beat-num">' + (i + 1) + " / " + data.beats.length + "</p>" +
          '<p class="beat-text">' + esc(b.text || "") + "</p>" +
        "</div>" +
      "</section>")
    .join("");
  story.scrollTop = 0;

  const beats = storyRail.querySelectorAll(".beat");
  if (storyObserver) storyObserver.disconnect();
  const io = new IntersectionObserver(
    (entries) => entries.forEach((en) => { if (en.isIntersecting) en.target.classList.add("in"); }),
    { root: story, threshold: 0.55 }
  );
  storyObserver = io;
  const usedIds = new Set();   // so two beats never show the same picture
  beats.forEach((el, i) => {
    io.observe(el);
    fetchImages(data.beats[i].imageQuery, 4).then((imgs) => {
      const pick = imgs.find((im) => !usedIds.has(im.id || im.thumb)) || imgs[0];
      if (pick) {
        usedIds.add(pick.id || pick.thumb);
        el.querySelector(".beat-bg").style.backgroundImage =
          "url('" + (pick.full || pick.thumb).replace(/'/g, "%27") + "')";
      }
    });
  });
  if (beats[0]) beats[0].classList.add("in");
}

function startJourney() {
  dossier.hidden = true;
  journey.hidden = false;
  jCountry.textContent = currentCountry;
  bgActiveEl = null;
  buildTimeline();
  goToEra(0);
  warmAllEras();          // prefetch every era's photos in the background → instant timeline
  Sound.startAmbient();
}

// Quietly warm each era's images, staggered so we don't hammer Wikimedia at once.
function warmAllEras() {
  currentEras.forEach((e, i) => {
    if (Array.isArray(e.images) || e._imgPromise) return;
    setTimeout(() => { if (!journey.hidden) ensureEraImages(i); }, 700 + i * 450);
  });
}

dossierBegin.addEventListener("click", startJourney);
dossierExit.addEventListener("click", exitJourney);

/* ====================== ERA JOURNEY ====================== */

// Fetch several queries and interleave them so the gallery mixes subjects.
// Turn a search query into a clean, simple caption (the subject of the photo).
function cleanSubject(q) {
  const s = String(q || "").replace(/\s+/g, " ").trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
}

// One DISTINCT photo per subject — never the same picture (or subject) twice.
async function fetchVariedImages(queries, max) {
  const qs = [], seenQ = new Set();
  for (const q of queries) {                          // drop duplicate/blank queries
    const c = (q || "").trim().toLowerCase();
    if (c && !seenQ.has(c)) { seenQ.add(c); qs.push(q); }
  }
  const use = qs.slice(0, Math.max(max, 8));
  const lists = await Promise.all(use.map((q) => fetchImages(q, 4)));
  const out = [], seen = new Set();
  for (let k = 0; k < lists.length && out.length < max; k++) {
    for (const im of lists[k]) {                      // first not-yet-used photo for this subject
      const id = im.id || im.thumb;
      if (seen.has(id)) continue;
      seen.add(id);
      out.push(Object.assign({}, im, { caption: subjectCaption(use[k]) }));
      break;                                          // exactly one per subject
    }
  }
  return out;
}

// Clean caption: the subject, minus a redundant trailing country name.
function subjectCaption(q) {
  let cap = cleanSubject(q);
  const c = (currentCountry || "").trim();
  if (c && cap.toLowerCase().endsWith(" " + c.toLowerCase())) cap = cap.slice(0, -(c.length + 1)).trim();
  return cap || cleanSubject(q);   // never blank (e.g. if the query was just the country name)
}

// Fetch (once) an era's images and cache them on the era object. Shared promise
// dedupes concurrent calls so preloading a neighbour can't double-fetch.
function ensureEraImages(i) {
  const era = currentEras[i];
  if (!era) return Promise.resolve([]);
  if (Array.isArray(era.images)) return Promise.resolve(era.images);
  if (!era._imgPromise) {
    const qs = (Array.isArray(era.imageQueries) && era.imageQueries.length)
      ? [era.imageQuery].concat(era.imageQueries).filter(Boolean)
      : [era.imageQuery, era.title + " " + currentCountry, currentCountry + " " + (era.period || ""), era.title].filter(Boolean);
    era._imgPromise = fetchVariedImages(qs, 7).then((imgs) => { era.images = imgs; return imgs; });
  }
  return era._imgPromise;
}

let storyWarmTimer = null;
async function goToEra(index) {
  if (index < 0 || index >= currentEras.length) return;
  currentEra = index;
  const era = currentEras[index];
  updateTimeline();
  updateArrows();

  // Render the text INSTANTLY (don't wait on images) so navigation feels immediate.
  eraStage.classList.remove("show");
  eraStage.innerHTML = stageHtml(era, index);
  void eraStage.offsetWidth;
  eraStage.classList.add("show");

  // Warm neighbours (instant prev/next), wire the legend prefetch, and warm the
  // legend itself after a short dwell so opening it is near-instant.
  ensureEraImages(index + 1);
  ensureEraImages(index - 1);
  const cta = eraStage.querySelector(".story-cta");
  if (cta) cta.addEventListener("mouseenter", () => prefetchStory(index), { once: true });
  clearTimeout(storyWarmTimer);
  storyWarmTimer = setTimeout(() => { if (currentEra === index && !journey.hidden) prefetchStory(index); }, 1200);

  // Fill the photo album as soon as the images are ready.
  await fillAlbum(era, index);
}

async function fillAlbum(era, index) {
  const imgs = Array.isArray(era.images) ? era.images : await ensureEraImages(index);
  if (currentEra !== index || journey.hidden) return;   // user moved on — drop this stale fill
  const album = document.getElementById("era-album");
  if (!album) return;
  setBackdrop(imgs[0] ? imgs[0].thumb : null);
  if (!imgs.length) {
    album.outerHTML = '<p class="album-empty">No archive images found for this era.</p>';
    return;
  }
  album.innerHTML = imgs.map((im, i) => coverHtml(im, i === 0)).join("");
  const update = () => applyCoverflow(album);
  album.addEventListener("scroll", () => requestAnimationFrame(update), { passive: true });
  album.querySelectorAll("img").forEach((img) => {
    const done = () => { img.classList.add("loaded"); update(); };
    if (img.complete) done(); else { img.addEventListener("load", done); img.addEventListener("error", done); }
  });
  requestAnimationFrame(update);
  setTimeout(update, 350);
}

function stageHtml(era, index) {
  return (
    '<div class="era-copy">' +
      '<div class="era-eyebrow">Era ' + toRoman(index + 1) + " · " + esc(era.period || "") + "</div>" +
      '<h2 class="era-h">' + esc(era.title || "") + "</h2>" +
      '<p class="era-p">' + esc(era.summary || "") + "</p>" +
    "</div>" +
    '<div class="album" id="era-album"></div>' +
    '<button class="story-cta" data-story="' + index + '">❧ &nbsp;Hear the legend of this era</button>'
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
  dossier.hidden = true;
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
  // Story sits on top of the journey — Escape closes the story; don't let arrows
  // leak through and change the era underneath it.
  if (!story.hidden) { if (e.key === "Escape") closeStory(); return; }
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
// Word-boundaried so it drops the dull stuff WITHOUT nuking legitimate photos
// whose names merely contain a substring (e.g. "chart" in Chartres, "flag" in
// flagship, "map" in Mapuche, "plan" in Planalto).
const JUNK_IMAGE = /(\bmaps?\b|locator|\bflags?\b|coat[\s_-]?of[\s_-]?arms|\bseal\b|\bemblem|\blogo|\bdiagram|\bcharts?\b|flowchart|\bicon\b|orthographic|\blocation\b|topograph|administ|\bblank\b|\boutline\b|\bgpx\b|wikimedia|spreadsheet|\bsignature\b|\bplan\b|schematic|\bsketch\b)/i;
const IMG_CACHE = new Map();   // cache searches so pages don't refetch the same query

async function fetchImages(query, max = 6) {
  if (!query) return [];
  const cacheKey = query + "|" + max;
  if (IMG_CACHE.has(cacheKey)) return IMG_CACHE.get(cacheKey);
  const params = new URLSearchParams({
    action: "query", format: "json", origin: "*",
    generator: "search", gsrsearch: query, gsrnamespace: "6", gsrlimit: "14",
    prop: "imageinfo", iiprop: "url|mime|size", iiurlwidth: "700",
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
    // Lightbox image: a 1280px thumb (derived from the thumb URL) rather than the
    // raw original, which can be many megabytes and slow to open.
    const full = (info.thumburl && /\/\d+px-/.test(info.thumburl))
      ? info.thumburl.replace(/\/\d+px-/, "/1280px-")
      : (info.url || thumb);
    const title = page.title || "";
    if (JUNK_IMAGE.test(title)) return;
    const w = info.width || 0, h = info.height || 0;
    if (w && w < 500) return;                         // skip tiny / thumbnail-only
    const area = w && h ? w * h : 500 * 500;
    const ratio = w && h ? Math.min(w, h) / Math.max(w, h) : 0.6; // 1 = square, →0 = sliver
    // favour big, well-proportioned, still-relevant images ("most intriguing")
    const score = Math.log(area) + ratio * 1.4 - i * 0.04;
    let caption = title.split(":").slice(1).join(":").replace(/\.[^.]+$/, "").replace(/_/g, " ").trim();
    caption = caption
      .split(/\s[-–—]\s/)[0]                              // drop "- Archivio..." tails
      .replace(/\([^)]*\d[^)]*\)/g, "")                   // drop "(47902649251)" code parens
      .replace(/,?\s*photo\s+\d+\s+of\s+\d+/i, "")        // drop "photo 3 of 8"
      .replace(/\s{2,}/g, " ").replace(/[,\s]+$/, "").trim();
    candidates.push({ thumb, full, caption, score, id: title || thumb });
  });

  candidates.sort((a, b) => b.score - a.score);
  const result = candidates.slice(0, max).map(({ thumb, full, caption, id }) => ({ thumb, full, caption, id }));
  IMG_CACHE.set(cacheKey, result);
  return result;
}

function coverHtml(img, eager) {
  const caption = esc(img.caption || "");
  const load = eager ? 'fetchpriority="high" loading="eager"' : 'loading="lazy"';
  return (
    '<figure class="cover" data-full="' + esc(img.full || img.thumb) + '" data-caption="' + caption + '">' +
      "<img " + load + ' decoding="async" src="' + esc(img.thumb) + '" alt="' + caption + '" />' +
      (caption ? "<figcaption>" + caption + "</figcaption>" : "") +
    "</figure>"
  );
}

function applyCoverflow(album) {
  // Use untransformed layout (offsetLeft) + scrollLeft so reading positions never
  // forces a reflow off the transformed covers — smoother scrolling.
  const center = album.scrollLeft + album.clientWidth / 2;
  const half = album.clientWidth / 2 || 1;
  album.querySelectorAll(".cover").forEach((cover) => {
    const coverCenter = cover.offsetLeft + cover.offsetWidth / 2;
    const k = Math.max(-1.4, Math.min(1.4, (coverCenter - center) / half));
    const rot = -k * 38;
    const scale = 1 - Math.min(Math.abs(k), 1) * 0.32;
    const tz = -Math.abs(k) * 120;
    cover.style.transform = "translate3d(0,0," + tz + "px) rotateY(" + rot + "deg) scale(" + scale + ")";
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
  let ctx = null, master = null, ambient = null, muted = true;  // silent by default

  function ensure() {
    if (ctx) return ctx;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = muted ? 0 : 0.5;     // soft overall; silent if muted
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
soundBtn.textContent = Sound.isMuted() ? "🔇" : "🔊";   // reflect the silent default
soundBtn.title = "Sound off — click for music";
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

/* ====================== OPEN ON PHONE (QR) ====================== */
(function setupPhoneQR() {
  const btn = document.getElementById("phone-btn");
  const card = document.getElementById("phone-card");
  const closeBtn = document.getElementById("phone-close");
  const qr = document.getElementById("phone-qr");
  const urlEl = document.getElementById("phone-url");
  const noteEl = card && card.querySelector(".phone-note");
  if (!btn || !card) return;

  function enable(url, local) {
    if (!url) return;
    btn.hidden = false;
    btn.onclick = () => {
      qr.src = "https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=12&data=" + encodeURIComponent(url);
      urlEl.textContent = url;
      if (noteEl) noteEl.textContent = local
        ? "Point your phone camera here. Phone must be on the same Wi‑Fi."
        : "Point your phone camera here — opens anywhere.";
      card.hidden = false; btn.hidden = true;
    };
    closeBtn.onclick = () => { card.hidden = true; btn.hidden = false; };
  }

  const host = location.hostname;
  if (host && host !== "localhost" && host !== "127.0.0.1") {
    enable(location.origin, false);          // published site → the QR just shares this URL
    return;
  }
  // running locally → ask the server for the Wi-Fi address (for same-network phones)
  let tries = 0;
  (function probe() {
    fetch("/api/lan").then((r) => r.json()).then((d) => {
      if (d && d.url) enable(d.url, true);
      else if (tries++ < 4) setTimeout(probe, 800);   // retry if the server wasn't ready yet
    }).catch(() => { if (tries++ < 4) setTimeout(probe, 800); });
  })();
})();

/* ====================== START ====================== */

initGlobe();
