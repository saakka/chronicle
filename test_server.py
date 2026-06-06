#!/usr/bin/env python3
"""Smoke tests for server.py — no external deps, no AI calls, no network.

Run:  python3 test_server.py    (exits 0 on pass, 1 on any failure)

Covers the server hardening: single-flight key_lock, do_HEAD, the /api/story
length cap, static serving, path-traversal defence, and 404s. Intentionally does
NOT hit the AI endpoints with valid params (those cost money / need a key).
"""
import os
import sys
import threading
import time
import http.client

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server  # noqa: E402
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

_order = []
def _same(tag):
    with server.key_lock("h:same"):
        _order.append(tag + "-in"); time.sleep(0.05); _order.append(tag + "-out")
_ts = [threading.Thread(target=_same, args=(t,)) for t in ("A", "B")]
[t.start() for t in _ts]; [t.join() for t in _ts]
check("key_lock: same key serializes (no overlap)",
      _order in (["A-in", "A-out", "B-in", "B-out"], ["B-in", "B-out", "A-in", "A-out"]))

_ev = []
def _diff(tag):
    with server.key_lock("h:" + tag):
        _ev.append(tag + "-in"); time.sleep(0.05); _ev.append(tag + "-out")
_td = [threading.Thread(target=_diff, args=(t,)) for t in ("X", "Y")]
[t.start() for t in _td]; [t.join() for t in _td]
check("key_lock: different keys run in parallel", _ev[0].endswith("-in") and _ev[1].endswith("-in"))

# ---- HTTP layer (non-AI endpoints only) --------------------------------------
_srv = ThreadingHTTPServer(("127.0.0.1", 8771), server.Handler)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
time.sleep(0.3)

def _req(method, path):
    cx = http.client.HTTPConnection("127.0.0.1", 8771, timeout=5)
    cx.request(method, path)
    r = cx.getresponse(); body = r.read(); cx.close()
    return r.status, body

s, b = _req("HEAD", "/");                                       check("HEAD / -> 200 with empty body", s == 200 and len(b) == 0)
s, b = _req("GET", "/api/ping");                                check("GET /api/ping -> 200 ok", s == 200 and b'"ok"' in b)
s, b = _req("GET", "/api/story?country=Spain&era=" + "x" * 90); check("oversized era -> 400 (length cap)", s == 400)
s, b = _req("GET", "/api/story?country=Spain");                 check("story missing era -> 400", s == 400)
s, b = _req("GET", "/");                                         check("GET / -> 200 static index", s == 200 and b"Chronicle" in b)
s, b = _req("GET", "/../server.py");                            check("path traversal -> not served (no 200)", s != 200)
s, b = _req("GET", "/nope.txt");                                check("missing file -> 404", s == 404)

_srv.shutdown()

print()
print("RESULT:", "ALL PASS" if not _failures else ("FAILED: " + ", ".join(_failures)))
sys.exit(0 if not _failures else 1)
