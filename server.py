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

import json
import os
import sys
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


def fetch_country_profile(country):
    """Ask Gemini for an original country profile. Returns (data, error)."""
    if not GEMINI_KEY:
        return None, "No Gemini key set (add gemini-key.txt)."
    body = {
        "contents": [{"parts": [{"text": PROFILE_PROMPT + country}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": PROFILE_SCHEMA,
            "temperature": 0.8,
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
        return None, "The profile service rejected the request (check the Gemini key)."
    except Exception as err:  # noqa: BLE001
        print("Gemini error: %r" % err, file=sys.stderr)
        return None, "Could not reach the profile service."

# ---------------------------------------------------------------------------
# The instructions and output shape we send to the AI
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a meticulous historian and visual curator.

Given a country, produce exactly 10 of the most historically significant ERAS in \
that country's history, ordered chronologically from earliest to most recent. \
Together they should tell the country's whole story at a glance.

For each era provide:
- "title": the name of the era or period.
- "period": its approximate date range, e.g. "c. 3100-2686 BCE", "1789-1815", or \
"1947-present".
- "summary": 2-3 clear, plain-language sentences on what defined this era and why \
it matters.
- "imageQuery": a short search phrase (2 to 5 words) naming a CONCRETE, photographable \
subject strongly tied to this era — a famous monument, artifact, ruler, artwork, \
battle, building, or place — that would return good results in an image archive. \
Strongly prefer well-known proper nouns (e.g. "Great Pyramid of Giza", \
"Tutankhamun gold mask", "Colosseum Rome", "Berlin Wall"). Include the country or \
place name when it helps disambiguate.

Be historically accurate; never invent. Return exactly 10 eras."""

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
                    "summary": {"type": "string"},
                    "imageQuery": {"type": "string"},
                },
                "required": ["title", "period", "summary", "imageQuery"],
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
        "model": MODEL,
        "max_tokens": 8000,
        "thinking": {"type": "adaptive"},
        "system": SYSTEM_PROMPT,
        "output_config": {
            "effort": "medium",
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
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the terminal quiet

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/history":
            self.handle_history(parse_qs(parsed.query))
        elif parsed.path == "/api/profile":
            self.handle_profile(parse_qs(parsed.query))
        else:
            self.serve_static(parsed.path)

    def send_json(self, status, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

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

        eras = data.get("eras", [])
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
        result = {"country": country, "profile": data}
        PROFILE_CACHE[key] = result
        self.send_json(200, result)

    def serve_static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        safe = os.path.normpath(path).lstrip("/\\")
        full = os.path.join(PUBLIC_DIR, safe)
        if not os.path.abspath(full).startswith(PUBLIC_DIR) or not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        ext = os.path.splitext(full)[1]
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = "http://localhost:%d" % PORT
    print("\n  📜  Chronicle — an illustrated history explorer")
    print("  Running at: %s" % url)
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
