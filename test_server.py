#!/usr/bin/env python3
"""Smoke tests for server.py — no external deps, no real AI calls, no public network.

Run:  python3 test_server.py    (exits 0 on pass, 1 on any failure)

Covers the server hardening: single-flight key_lock, do_HEAD, the /api/story length
cap, static serving + path-traversal defence, 404s, AND (via a monkeypatched fetch,
so no real/paid AI call) the handler success path, caching, the HEAD-never-generates
guard, and the daily-budget refund-on-failure.
"""
import os
import sys
import threading
import time
import http.client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server  # noqa: E402  (reads keys into memory but never prints them; main() isn't run on import)
from http.server import ThreadingHTTPServer  # noqa: E402

_failures = []


def check(name, ok):
    print(("PASS" if ok else "FAIL"), "-", name)
    if not ok:
        _failures.append(name)


# ---- single-flight lock (key_lock) -------------------------------------------
a, b, c = server.key_lock("h:x"), server.key_lock("h:x"), server.key_lock("p:x")
check("key_lock: same key shares one lock", a is b)
check("key_lock: different keys are independent", a is not c)

# same key must serialize: with a sleep inside the lock, order is strictly non-interleaved
_order = []
def _same(tag):
    with server.key_lock("h:same"):
        _order.append(tag + "-in"); time.sleep(0.05); _order.append(tag + "-out")
_ts = [threading.Thread(target=_same, args=(t,)) for t in ("A", "B")]
[t.start() for t in _ts]; [t.join() for t in _ts]
check("key_lock: same key serializes (no overlap)",
      _order in (["A-in", "A-out", "B-in", "B-out"], ["B-in", "B-out", "A-in", "A-out"]))

# different keys must run in parallel — DETERMINISTIC via a barrier (no sleep-timing races):
# both threads, each holding its own (distinct) lock, must reach the barrier at once. If the two
# keys wrongly shared a lock, the second could never enter, the barrier would time out, and the
# count would be < 2.
_barrier = threading.Barrier(2, timeout=2)
_both_in = []
def _diff(tag):
    with server.key_lock("h:" + tag):
        try:
            _barrier.wait()
            _both_in.append(tag)
        except threading.BrokenBarrierError:
            pass
_td = [threading.Thread(target=_diff, args=(t,)) for t in ("X", "Y")]
[t.start() for t in _td]; [t.join() for t in _td]
check("key_lock: different keys run in parallel (both held at once)", len(_both_in) == 2)

# ---- HTTP layer --------------------------------------------------------------
ThreadingHTTPServer.allow_reuse_address = True
try:
    _srv = ThreadingHTTPServer(("127.0.0.1", 8771), server.Handler)
except OSError as e:
    print("FAIL - could not bind test port 8771:", e)
    sys.exit(1)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
time.sleep(0.3)

def _req(method, path):
    cx = http.client.HTTPConnection("127.0.0.1", 8771, timeout=5)
    cx.request(method, path)
    r = cx.getresponse(); body = r.read(); cx.close()
    return r.status, body

try:
    # --- non-AI endpoints ---
    s, b = _req("HEAD", "/");                                       check("HEAD / -> 200 with empty body", s == 200 and len(b) == 0)
    s, b = _req("GET", "/api/ping");                                check("GET /api/ping -> 200 ok", s == 200 and b'"ok"' in b)
    s, b = _req("GET", "/api/story?country=Spain&era=" + "x" * 90); check("oversized era -> 400 (length cap)", s == 400)
    s, b = _req("GET", "/api/story?country=Spain");                 check("story missing era -> 400", s == 400)
    s, b = _req("GET", "/");                                         check("GET / -> 200 static index", s == 200 and b"Chronicle" in b)
    s, b = _req("GET", "/nope.txt");                                check("missing file -> 404", s == 404)

    # path traversal: server.py source (and the API key it reads) must NEVER be served, via any
    # encoding. Assert no 200 AND no server-source bytes leak across several traversal payloads.
    leaked = False
    for trav in ("/../server.py", "/static/../../server.py", "/%2e%2e/server.py", "/..%2fserver.py", "/....//server.py"):
        st, bd = _req("GET", trav)
        if st == 200 or b"fetch_history_from_ai" in bd or b"API_KEY" in bd:
            leaked = True
    check("path traversal: server.py source never served (any payload)", not leaked)

    # --- handler success / caching / HEAD-no-AI / refund-on-failure -----------
    # Monkeypatch the AI fetch so NO real (paid) call is made; exercise the full
    # cache -> key_lock -> generate -> cache -> send-outside-lock path.
    _orig_key, _orig_fetch = server.API_KEY, server.fetch_history_from_ai
    server.API_KEY = "test-key"   # leave demo mode so the handler takes the real path
    try:
        server.CACHE.clear()
        server.fetch_history_from_ai = lambda c: ({"country": c, "eras": [{"title": "Era I", "period": "x"}]}, None)
        s, b = _req("GET", "/api/history?country=Testlandia")
        check("history success path -> 200 with eras", s == 200 and b'"eras"' in b and b"Era I" in b)
        s2, b2 = _req("GET", "/api/history?country=Testlandia")
        check("history second request served from cache (identical)", s2 == 200 and b2 == b)

        # HEAD must NOT generate (Fix #1): patch fetch to blow up if it's ever called on a HEAD.
        server.CACHE.clear()
        server.fetch_history_from_ai = lambda c: (_ for _ in ()).throw(AssertionError("AI called on HEAD"))
        s, b = _req("HEAD", "/api/history?country=Uncached")
        check("HEAD /api/history -> 200, no body, NO AI call (Fix #1)", s == 200 and len(b) == 0 and "Uncached".lower() not in server.CACHE)

        # Failure must REFUND the daily slot (Fix #2): reserve+refund nets zero.
        server.CACHE.clear()
        server.fetch_history_from_ai = lambda c: (None, "simulated AI failure")
        before = server._DAILY["count"]
        s, b = _req("GET", "/api/history?country=Failistan")
        after = server._DAILY["count"]
        check("AI failure -> 502", s == 502)
        check("AI failure refunds the daily slot (Fix #2)", after == before)
    finally:
        server.API_KEY, server.fetch_history_from_ai = _orig_key, _orig_fetch
finally:
    _srv.shutdown()
    _srv.server_close()   # release the listening socket so re-runs can rebind cleanly

print()
print("RESULT:", "ALL PASS" if not _failures else ("FAILED: " + ", ".join(_failures)))
sys.exit(0 if not _failures else 1)
