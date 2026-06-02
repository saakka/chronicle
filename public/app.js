/* ---------------------------------------------------------------------------
   Chronicle — a planet of history
   - A draggable 3D globe (Radio-Garden style). Click a country to open it.
   - History view: 10 eras, each an iPhone "Cover Flow" photo carousel.
   Images are fetched in the browser from Wikimedia Commons.
--------------------------------------------------------------------------- */

const globeView = document.getElementById("globe-view");
const globeFallback = document.getElementById("globe-fallback");
const historyView = document.getElementById("history-view");
const backBtn = document.getElementById("back-btn");
const statusEl = document.getElementById("status");
const headingEl = document.getElementById("result-heading");
const erasEl = document.getElementById("eras");

const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightbox-img");
const lightboxCaption = document.getElementById("lightbox-caption");
const lightboxClose = lightbox.querySelector(".lightbox-close");

// The 22 Arab League countries — all live. Click any marker to explore.
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

const GLOBE_POINTS = ARAB_COUNTRIES.map((c) => ({
  country: c.country,
  lat: c.lat,
  lng: c.lng,
  color: "#ffcf57",
  size: 0.5,
  label: c.country,
}));

let world = null;

/* ====================== GLOBE ====================== */

function initGlobe() {
  const el = document.getElementById("globe");
  if (typeof Globe === "undefined" || !el) return showFallback();

  try {
    world = Globe()(el)
      .backgroundColor("rgba(0,0,0,0)")
      .globeImageUrl("https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg")
      .bumpImageUrl("https://unpkg.com/three-globe/example/img/earth-topology.png")
      .pointsData(GLOBE_POINTS)
      .pointLat("lat").pointLng("lng").pointColor("color")
      .pointAltitude(0.03).pointRadius("size")
      .pointLabel("label")
      .onPointClick((p) => openCountry(p.country))
      // pulsing golden ring on each live country
      .ringsData(GLOBE_POINTS)
      .ringLat("lat").ringLng("lng")
      .ringColor(() => (t) => "rgba(255,207,87," + (1 - t) + ")")
      .ringMaxRadius(6).ringPropagationSpeed(2.5).ringRepeatPeriod(1100);
  } catch (err) {
    console.error("Globe init failed:", err);
    return showFallback();
  }

  sizeGlobe();
  const controls = world.controls();
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.5;
  controls.minDistance = 180;
  world.pointOfView({ lat: 24, lng: 42, altitude: 2.1 }, 0);

  // stop the gentle spin once the user grabs the planet
  el.addEventListener("pointerdown", () => { controls.autoRotate = false; });
  window.addEventListener("resize", sizeGlobe);
}

function sizeGlobe() {
  if (world) world.width(window.innerWidth).height(window.innerHeight);
}

function showFallback() {
  if (!globeFallback) return;
  globeFallback.hidden = false;
  globeFallback.innerHTML =
    '<div class="fallback-inner">' +
      "<p>Choose a country:</p>" +
      '<div class="fallback-list">' +
        ARAB_COUNTRIES.map(
          (c) => '<button class="chip" data-country="' + esc(c.country) + '">' + esc(c.country) + "</button>"
        ).join("") +
      "</div>" +
    "</div>";
}

/* ====================== VIEW SWITCHING ====================== */

document.addEventListener("click", (event) => {
  const trigger = event.target.closest("[data-country]");
  if (trigger) openCountry(trigger.getAttribute("data-country"));
});

backBtn.addEventListener("click", () => {
  historyView.hidden = true;
  globeView.style.display = "";
  sizeGlobe();
});

async function openCountry(country) {
  globeView.style.display = "none";
  historyView.hidden = false;
  window.scrollTo(0, 0);
  erasEl.innerHTML = "";
  headingEl.textContent = country;
  setStatus("Assembling the history of " + country + " — this can take a moment…", "loading");

  try {
    const res = await fetch("/api/history?country=" + encodeURIComponent(country));
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    render(data);
  } catch (err) {
    if (err instanceof TypeError) {
      setStatus("Can't reach the server. Make sure the app is running.", "error");
    } else {
      setStatus(err.message, "error");
    }
  }
}

function setStatus(text, kind) {
  statusEl.textContent = text;
  statusEl.className = "status" + (kind ? " " + kind : "");
}

/* ====================== RENDER ERAS ====================== */

function render(data) {
  const eras = Array.isArray(data.eras) ? data.eras : [];
  if (eras.length === 0) {
    setStatus("No history was returned. Please try again.", "error");
    return;
  }

  headingEl.textContent = data.country;
  setStatus(
    data.demo ? "Demo mode: built-in Egypt sample (add an API key for any country)." : "",
    data.demo ? "demo" : ""
  );

  eras.forEach((era, index) => {
    const { section, slot } = buildEra(era, index);
    erasEl.appendChild(section);
    loadAlbum(slot, era.imageQuery || era.title || "");
  });
}

function buildEra(era, index) {
  const section = document.createElement("section");
  section.className = "era";
  section.style.animationDelay = Math.min(index * 0.05, 0.6) + "s";

  section.innerHTML =
    '<div class="era-head">' +
      '<span class="era-num">' + toRoman(index + 1) + "</span>" +
      '<h3 class="era-title">' + esc(era.title || "") + "</h3>" +
    "</div>" +
    '<p class="era-period">' + esc(era.period || "") + "</p>" +
    '<p class="era-summary">' + esc(era.summary || "") + "</p>" +
    '<div class="album-slot"><p class="album-empty">Gathering images…</p></div>';

  return { section, slot: section.querySelector(".album-slot") };
}

async function loadAlbum(slot, query) {
  const images = await fetchImages(query);
  if (!images.length) {
    slot.innerHTML = '<p class="album-empty">No archive images found for this era.</p>';
    return;
  }
  slot.innerHTML = '<div class="album">' + images.map(coverHtml).join("") + "</div>";

  const album = slot.querySelector(".album");
  const update = () => applyCoverflow(album);
  album.addEventListener("scroll", () => requestAnimationFrame(update), { passive: true });
  album.querySelectorAll("img").forEach((img) => img.addEventListener("load", update));
  requestAnimationFrame(update);
  setTimeout(update, 350);
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

/* The Cover Flow effect: tilt + scale each cover by its distance from center. */
function applyCoverflow(album) {
  const rect = album.getBoundingClientRect();
  const center = rect.left + rect.width / 2;
  album.querySelectorAll(".cover").forEach((cover) => {
    const cr = cover.getBoundingClientRect();
    const coverCenter = cr.left + cr.width / 2;
    const d = (coverCenter - center) / (rect.width / 2); // -1 .. 1 across the view
    const k = Math.max(-1.4, Math.min(1.4, d));
    const rot = -k * 38;
    const scale = 1 - Math.min(Math.abs(k), 1) * 0.32;
    const tz = -Math.abs(k) * 120;
    cover.style.transform =
      "translateZ(" + tz + "px) rotateY(" + rot + "deg) scale(" + scale + ")";
    cover.style.zIndex = String(1000 - Math.round(Math.abs(k) * 1000));
    cover.style.opacity = String(1 - Math.min(Math.abs(k), 1) * 0.45);
  });
}

/* ====================== WIKIMEDIA IMAGES (browser-side) ====================== */

async function fetchImages(query, max = 6) {
  if (!query) return [];
  const params = new URLSearchParams({
    action: "query", format: "json", origin: "*",
    generator: "search", gsrsearch: query, gsrnamespace: "6", gsrlimit: "18",
    prop: "imageinfo", iiprop: "url|mime", iiurlwidth: "640",
  });
  let data;
  try {
    const res = await fetch("https://commons.wikimedia.org/w/api.php?" + params.toString());
    data = await res.json();
  } catch (err) {
    return [];
  }
  const pages = (data.query && data.query.pages) || {};
  const ordered = Object.values(pages).sort(
    (a, b) => (a.index == null ? 9999 : a.index) - (b.index == null ? 9999 : b.index)
  );
  const out = [];
  for (const page of ordered) {
    const info = (page.imageinfo && page.imageinfo[0]) || {};
    const mime = info.mime || "";
    if (!mime.startsWith("image/") || mime === "image/svg+xml") continue;
    const thumb = info.thumburl || info.url;
    if (!thumb) continue;
    const title = page.title || "";
    const caption = title.split(":").slice(1).join(":").replace(/\.[^.]+$/, "").replace(/_/g, " ").trim();
    out.push({ thumb: thumb, full: info.url || thumb, caption: caption });
    if (out.length >= max) break;
  }
  return out;
}

/* ====================== LIGHTBOX ====================== */

erasEl.addEventListener("click", (event) => {
  const fig = event.target.closest(".cover");
  if (!fig) return;
  openLightbox(fig.getAttribute("data-full"), fig.getAttribute("data-caption"));
});

function openLightbox(src, caption) {
  lightboxImg.src = src;
  lightboxImg.alt = caption || "";
  lightboxCaption.textContent = caption || "";
  lightbox.hidden = false;
}
function closeLightbox() {
  lightbox.hidden = true;
  lightboxImg.src = "";
}
lightboxClose.addEventListener("click", closeLightbox);
lightbox.addEventListener("click", (e) => { if (e.target === lightbox) closeLightbox(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !lightbox.hidden) closeLightbox(); });

/* ====================== HELPERS ====================== */

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
