"""
Chronicle — an illustrated history explorer.

What it does:
  - Serves the web page in the `public/` folder.
  - /api/history?country=NAME asks Claude for the 10 most significant ERAS of a
    country's history, then fetches real images for each era from Wikimedia
    Commons, and returns it all as JSON. The page shows each era as a photo album.

Why a server (and not just a web page)?
  Your secret API key must never live in the browser. This little server holds
  the key and talks to the AI (and to Wikimedia) on the page's behalf.

It uses ONLY Python's standard library — nothing to install.

Run it with:   python3 server.py    (or double-click start.command)
Then open:     http://localhost:8000
"""

import gzip
import json
import os
import socket
import sys
import threading
import time
import urllib.request
import urllib.error
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from demo_data import DEMO_HISTORY

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORT = int(os.environ.get("PORT", "8000"))
HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(HERE, "public")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-opus-4-8"
HISTORY_MODEL = "claude-haiku-4-5"    # fast: the 10-era list (no extended thinking)
WRITER_MODEL = "claude-haiku-4-5"     # fast prose for the short legend beats & profiles


def load_api_key():
    """Read the API key from the environment, a `.env` file, or `api-key.txt`."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    env_path = os.path.join(HERE, ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY"):
                    _, _, value = line.partition("=")
                    return value.strip().strip('"').strip("'")
    txt_path = os.path.join(HERE, "api-key.txt")
    if os.path.isfile(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content.startswith("sk-"):
            return content
    return ""


API_KEY = load_api_key()

# Cache results so we don't re-pay / re-fetch for the same country.
CACHE = {}
PROFILE_CACHE = {}

# --- Simple rate limiting (protects your API bill when the link is public) ---
RATE_WINDOW = 60.0          # seconds
RATE_PER_IP = int(os.environ.get("RATE_PER_IP", "20"))      # AI calls per window, per visitor
RATE_GLOBAL = int(os.environ.get("RATE_GLOBAL", "80"))      # AI calls per window, everyone combined
_RATE_LOCK = threading.Lock()
_RATE_BY_IP = {}            # ip -> [timestamps]
_RATE_GLOBAL = []           # [timestamps]


def rate_ok(ip):
    """True if this visitor (and the app overall) is under the per-minute AI-call cap."""
    now = time.monotonic()
    with _RATE_LOCK:
        _RATE_GLOBAL[:] = [t for t in _RATE_GLOBAL if now - t < RATE_WINDOW]
        if len(_RATE_GLOBAL) >= RATE_GLOBAL:
            return False
        hits = [t for t in _RATE_BY_IP.get(ip, []) if now - t < RATE_WINDOW]
        if len(hits) >= RATE_PER_IP:
            _RATE_BY_IP[ip] = hits
            return False
        hits.append(now)
        _RATE_BY_IP[ip] = hits
        _RATE_GLOBAL.append(now)
        return True


def load_gemini_key():
    """Gemini API key from env or gemini-key.txt (for the country profiles)."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    p = os.path.join(HERE, "gemini-key.txt")
    if os.path.isfile(p):
        with open(p, "r", encoding="utf-8") as f:
            s = f.read().strip()
        if s:
            return s
    return ""


GEMINI_KEY = load_gemini_key()
# Gemini's free tier is only ~20 requests/day; once it refuses (429) we flip this
# off and serve everything from Claude for the rest of the session.
GEMINI_OK = True
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % GEMINI_MODEL
)

# Original, in-depth country profile (own words — not copied from any source).
PROFILE_PROMPT = (
    "Write an ORIGINAL, accurate, richly detailed country profile for a history & geography web app, "
    "in a lively, witty, energetic tone for curious history geeks. Use ENTIRELY your own wording — do "
    "not copy any TV show, YouTube channel, or article. Be specific and substantive: 2-4 sentences per "
    "text field. For 'flagMeaning', explain what the flag's colours and symbols stand for. For "
    "'imageQueries', give 6 short search phrases naming concrete, photogenic subjects (famous landmarks, "
    "landscapes, cities, cultural scenes) that would find striking real photos — prefer proper nouns. "
    "Country: "
)
PROFILE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "officialName": {"type": "STRING"},
        "overview": {"type": "STRING"},
        "flagMeaning": {"type": "STRING"},
        "political": {"type": "STRING"},
        "physical": {"type": "STRING"},
        "demographics": {"type": "STRING"},
        "economy": {"type": "STRING"},
        "culture": {"type": "STRING"},
        "funFacts": {"type": "ARRAY", "items": {"type": "STRING"}},
        "imageQueries": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": [
        "officialName", "overview", "flagMeaning", "political", "physical",
        "demographics", "economy", "culture", "funFacts", "imageQueries",
    ],
}


# Anthropic-format (lowercase) schemas for the Claude fallback.
PROFILE_SCHEMA_CLAUDE = {
    "type": "object",
    "properties": {
        k: ({"type": "array", "items": {"type": "string"}} if k in ("funFacts", "imageQueries")
            else {"type": "string"})
        for k in ("officialName", "overview", "flagMeaning", "political", "physical",
                  "demographics", "economy", "culture", "funFacts", "imageQueries")
    },
    "required": ["officialName", "overview", "flagMeaning", "political", "physical",
                 "demographics", "economy", "culture", "funFacts", "imageQueries"],
    "additionalProperties": False,
}
STORY_SCHEMA_CLAUDE = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "beats": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "imageQuery": {"type": "string"}},
            "required": ["text", "imageQuery"], "additionalProperties": False}},
    },
    "required": ["title", "beats"],
    "additionalProperties": False,
}


def _gemini_json(prompt, schema, temperature):
    """Ask Gemini for JSON matching schema. Returns (data, error)."""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": temperature,
            # gemini-2.5-flash "thinks" by default (~10s). We just need a short JSON
            # legend, so switch thinking OFF — responses drop to ~1-2s.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    request = urllib.request.Request(
        GEMINI_URL + "?key=" + GEMINI_KEY,
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text), None
    except urllib.error.HTTPError as err:
        print("Gemini failed (%s): %s" % (err.code, err.read().decode("utf-8", "replace")), file=sys.stderr)
        return None, ("quota" if err.code == 429 else "http")
    except Exception as err:  # noqa: BLE001
        print("Gemini error: %r" % err, file=sys.stderr)
        return None, "error"


def _claude_json(prompt, schema, max_tokens=3500):
    """Ask Claude for JSON matching schema (the reliable fallback). Returns (data, error)."""
    if not API_KEY:
        return None, "No Anthropic key set (add api-key.txt)."
    body = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "output_config": {"format": {"type": "json_schema", "schema": schema}},
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json", "x-api-key": API_KEY,
                 "anthropic-version": "2023-06-01"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        print("Claude JSON failed (%s): %s" % (err.code, err.read().decode("utf-8", "replace")), file=sys.stderr)
        return None, "The AI service rejected the request."
    except Exception as err:  # noqa: BLE001
        print("Claude JSON error: %r" % err, file=sys.stderr)
        return None, "Could not reach the AI service."
    block = next((b for b in payload.get("content", []) if b.get("type") == "text"), None)
    if not block:
        return None, "The AI returned no usable answer."
    try:
        return json.loads(block["text"]), None
    except (ValueError, KeyError):
        return None, "The AI's answer was incomplete."


def fetch_country_profile(country):
    """Original country profile: Gemini first (free), Claude fallback. Returns (data, error)."""
    global GEMINI_OK
    prompt = PROFILE_PROMPT + country
    if GEMINI_KEY and GEMINI_OK:
        data, _ = _gemini_json(prompt, PROFILE_SCHEMA, 0.8)
        if data and data.get("overview"):
            return data, None
        GEMINI_OK = False  # out of free quota — switch to Claude for the session
    return _claude_json(prompt, PROFILE_SCHEMA_CLAUDE, 3000)


# --- Story mode: the flagship anecdote of an era, as scroll-through beats ---
STORY_CACHE = {}
STORY_PROMPT = (
    "Recount the single most famous true story or legend from this country's given historical era — "
    "the flagship tale a history lover would instantly recognise. Use ENTIRELY your own original wording "
    "(do not copy any book, show, or article). Be TIGHT, vivid and cinematic with NO filler or throat-clearing. "
    "Break it into 6 sequential BEATS. Each beat is ONE punchy sentence (about 18-28 words; never more than two "
    "very short sentences) that moves the story forward, plus an 'imageQuery': a short search phrase naming ONE "
    "striking, photographable subject for that beat — a specific monument, artifact, artwork, statue, building, "
    "ruin, or famous person (prefer proper nouns). Include the country or place name in the "
    "imageQuery when it sharpens the result (e.g. 'Charlemagne statue Aachen', not just 'statue'). "
    "NEVER a map, diagram, document, chart, stamp, banknote, or book cover. "
    "Country and era: "
)
STORY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "beats": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"text": {"type": "STRING"}, "imageQuery": {"type": "STRING"}},
                "required": ["text", "imageQuery"],
            },
        },
    },
    "required": ["title", "beats"],
}


def fetch_story(subject):
    """Flagship legend: Gemini first (free), Claude fallback. subject = 'Country — Era (period)'."""
    global GEMINI_OK
    prompt = STORY_PROMPT + subject
    if GEMINI_KEY and GEMINI_OK:
        data, _ = _gemini_json(prompt, STORY_SCHEMA, 0.9)
        if data and data.get("beats"):
            return data, None
        GEMINI_OK = False
    return _claude_json(prompt, STORY_SCHEMA_CLAUDE, 3500)

# ---------------------------------------------------------------------------
# The instructions and output shape we send to the AI
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a meticulous historian.

Given a country, produce exactly 10 of the most historically significant ERAS in \
that country's history, ordered chronologically from earliest to most recent. \
Together they should tell the country's whole story at a glance — they become the \
chapters of an illustrated timeline.

For each era provide ONLY:
- "title": the SHORT, widely-recognised name of that era, dynasty, kingdom, or period — the \
label a history lover instantly knows it by (e.g. "Abbasid Caliphate", "Meiji Era", "Viking \
Age", "Mughal Empire", "Old Kingdom", "Edo Period", "Ottoman Empire"). Make it iconic and \
concise: at most ~4 words; NO descriptions and NO "and"-joined compounds.
- "period": its approximate date range, e.g. "c. 3100-2686 BCE", "1789-1815", or \
"1947-present".

Be historically accurate; never invent. Keep it terse — titles and dates only, no \
descriptions. Return exactly 10 eras."""

SCHEMA = {
    "type": "object",
    "properties": {
        "country": {"type": "string"},
        "eras": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "period": {"type": "string"},
                },
                "required": ["title", "period"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["country", "eras"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Talking to the AI
# ---------------------------------------------------------------------------

def fetch_history_from_ai(country):
    """Ask Claude for the country's 10 eras. Returns (data, error_message)."""
    body = {
        "model": HISTORY_MODEL,
        "max_tokens": 1200,    # 10 eras of title+period only — small + fast
        "system": SYSTEM_PROMPT,
        "output_config": {
            "format": {"type": "json_schema", "schema": SCHEMA},
        },
        "messages": [{"role": "user", "content": "Country: " + country}],
    }

    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")
        print("AI request failed (%s): %s" % (err.code, detail), file=sys.stderr)
        if err.code == 401:
            return None, "Your API key was rejected. Check the key in api-key.txt."
        if err.code == 429:
            return None, "The AI service is busy (rate limit). Wait a moment and retry."
        return None, "There was a problem reaching the AI service. Please try again."
    except Exception as err:  # noqa: BLE001
        print("AI request error: %r" % err, file=sys.stderr)
        return None, "Could not reach the AI service. Check your internet connection."

    if payload.get("stop_reason") == "refusal":
        return None, "The AI declined this request. Try a different country."

    text_block = next(
        (b for b in payload.get("content", []) if b.get("type") == "text"), None
    )
    if not text_block:
        return None, "The AI returned no usable answer. Please try again."

    try:
        data = json.loads(text_block["text"])
    except (ValueError, KeyError):
        return None, "The AI's answer was incomplete. Please try again."

    return data, None


# ---------------------------------------------------------------------------
# The web server
#
# Note: images are NOT fetched here. The browser pulls them from Wikimedia
# Commons directly (using each era's "imageQuery"), which keeps this server
# simple and works even where the server can't reach the image archive.
# ---------------------------------------------------------------------------

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
}


GZIP_TYPES = {
    "text/html", "text/css", "application/javascript",
    "application/json", "image/svg+xml", "text/plain",
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # persistent connections → faster back-to-back requests

    def log_message(self, *args):
        pass  # keep the terminal quiet

    def _write_payload(self, status, ctype, raw, cache_control=None):
        """Send bytes — gzip-compressing text when the client supports it — always with a
        correct Content-Length so keep-alive works."""
        body = raw
        gz = (ctype.split(";")[0].strip() in GZIP_TYPES
              and "gzip" in self.headers.get("Accept-Encoding", "")
              and len(raw) >= 600)
        if gz:
            body = gzip.compress(raw, 6)
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        if gz:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        if cache_control:
            self.send_header("Cache-Control", cache_control)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def client_ip(self):
        xff = self.headers.get("X-Forwarded-For", "")
        # Use the RIGHTMOST hop (the one Render's proxy appended), not the client-controlled
        # leftmost value — so X-Forwarded-For can't be spoofed to dodge the per-IP limit.
        return xff.split(",")[-1].strip() if xff else self.client_address[0]

    def do_GET(self):
        parsed = urlparse(self.path)
        # Cap the AI-backed endpoints so a public link can't run up the bill.
        if parsed.path in ("/api/history", "/api/profile", "/api/story") and not rate_ok(self.client_ip()):
            self.send_json(429, {"error": "Lots of explorers right now — please wait a minute and try again."})
            return
        if parsed.path == "/api/history":
            self.handle_history(parse_qs(parsed.query))
        elif parsed.path == "/api/profile":
            self.handle_profile(parse_qs(parsed.query))
        elif parsed.path == "/api/story":
            self.handle_story(parse_qs(parsed.query))
        elif parsed.path == "/api/ping":
            self.send_json(200, {"ok": True})   # cheap wake-up ping (no AI, not rate-limited)
        elif parsed.path == "/api/lan":
            ip = local_ip()
            self.send_json(200, {"ip": ip or "", "url": ("http://%s:%d" % (ip, PORT)) if ip else ""})
        else:
            self.serve_static(parsed.path)

    def send_json(self, status, obj):
        self._write_payload(status, "application/json; charset=utf-8",
                             json.dumps(obj).encode("utf-8"), cache_control="no-store")

    def handle_history(self, query):
        country = (query.get("country", [""])[0] or "").strip()
        if not country:
            self.send_json(400, {"error": "Please enter a country name."})
            return
        if len(country) > 60:
            self.send_json(400, {"error": "That name looks too long."})
            return

        # No API key? Run in demo mode with built-in sample text (images still
        # come live from Wikimedia, so it stays visual).
        if not API_KEY:
            self.send_json(200, {
                "demo": True,
                "country": DEMO_HISTORY["country"],
                "eras": DEMO_HISTORY["eras"],
            })
            return

        cache_key = country.lower()
        if cache_key in CACHE:
            self.send_json(200, CACHE[cache_key])
            return

        data, error = fetch_history_from_ai(country)
        if error:
            self.send_json(502, {"error": error})
            return

        eras = data.get("eras") if isinstance(data, dict) else None
        if not isinstance(eras, list) or not eras:
            # Don't cache an empty/garbled answer — let the next attempt retry.
            self.send_json(502, {"error": "The AI's answer was incomplete. Please try again."})
            return
        result = {"demo": False, "country": data.get("country", country), "eras": eras}
        CACHE[cache_key] = result
        self.send_json(200, result)

    def handle_profile(self, query):
        country = (query.get("country", [""])[0] or "").strip()
        if not country:
            self.send_json(400, {"error": "Please enter a country name."})
            return
        if len(country) > 60:
            self.send_json(400, {"error": "That name looks too long."})
            return
        key = country.lower()
        if key in PROFILE_CACHE:
            self.send_json(200, PROFILE_CACHE[key])
            return
        data, error = fetch_country_profile(country)
        if error:
            self.send_json(502, {"error": error})
            return
        if not isinstance(data, dict) or not data.get("overview"):
            self.send_json(502, {"error": "The profile came back empty. Please try again."})
            return
        result = {"country": country, "profile": data}
        PROFILE_CACHE[key] = result
        self.send_json(200, result)

    def handle_story(self, query):
        country = (query.get("country", [""])[0] or "").strip()
        era = (query.get("era", [""])[0] or "").strip()
        period = (query.get("period", [""])[0] or "").strip()
        if not country or not era:
            self.send_json(400, {"error": "Need a country and an era."})
            return
        key = (country + "|" + era).lower()
        if key in STORY_CACHE:
            self.send_json(200, STORY_CACHE[key])
            return
        subject = "%s — %s%s" % (country, era, (" (" + period + ")") if period else "")
        data, error = fetch_story(subject)
        if error:
            self.send_json(502, {"error": error})
            return
        beats = data.get("beats") if isinstance(data, dict) else None
        if not isinstance(beats, list) or not beats:
            self.send_json(502, {"error": "The story came back empty. Please try again."})
            return
        result = {"country": country, "era": era, "story": data}
        STORY_CACHE[key] = result
        self.send_json(200, result)

    def serve_static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        if path == "/favicon.ico":
            self.send_response(204)  # no icon file — silence the browser's 404
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        public_root = os.path.abspath(PUBLIC_DIR)
        safe = os.path.normpath(path).lstrip("/\\")
        full = os.path.abspath(os.path.join(public_root, safe))
        # must resolve to something strictly inside public/ (defence-in-depth)
        if not (full == public_root or full.startswith(public_root + os.sep)) or not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        ext = os.path.splitext(full)[1]
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
        with open(full, "rb") as f:
            data = f.read()
        if ext in (".html", ".htm"):
            cache = "no-cache"                  # always revalidate the page shell
        elif ext in (".css", ".js"):
            cache = "public, max-age=600"       # 10 min — snappy repeat visits
        else:
            cache = "public, max-age=86400"     # images, fonts, etc.
        self._write_payload(200, ctype, data, cache_control=cache)


def local_ip():
    """Best-effort LAN IP so phones on the same Wi-Fi can reach the app."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))   # no packets are actually sent
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def main():
    # Listen on all interfaces so other devices (your phone) on the same Wi-Fi can connect.
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    url = "http://localhost:%d" % PORT
    ip = local_ip()
    print("\n  📜  Chronicle — an illustrated history explorer")
    print("  On this Mac:        %s" % url)
    if ip:
        print("  On your phone:      http://%s:%d   (same Wi-Fi)" % (ip, PORT))
    if API_KEY:
        print("  Mode: LIVE — real histories + images for any country.\n")
    else:
        print("  Mode: DEMO — sample text (with live images).")
        print("        Add your API key to api-key.txt to explore any country.\n")
    print("  Press Ctrl+C to stop.\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped. Goodbye!\n")
        server.shutdown()


if __name__ == "__main__":
    main()
