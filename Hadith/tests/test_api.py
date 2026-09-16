"""Tests d'intégration : nécessitent la base ingérée et l'index construit (sinon ignorés)."""
import pytest
from fastapi.testclient import TestClient

from hadith_bot.arabic import strip_tashkil
from hadith_bot.api import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _ready(client) -> bool:
    h = client.get("/health").json()
    return h["hadiths"] > 0 and h["vectors"] > 0


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_ask_without_llm(client):
    if not _ready(client):
        pytest.skip("base non ingérée")
    r = client.post("/ask", json={"question": "إنما الأعمال بالنيات", "k": 3, "use_llm": False})
    assert r.status_code == 200
    d = r.json()
    assert d["results"] and d["answer"]
    top = d["results"][0]
    assert "chains" in top and top["chains"][0]["links"]
    # le hadith de la niyya (Bukhari 1 / 54, Muslim 4927 ...) doit être en tête
    assert any("بالني" in strip_tashkil(r["matn_ar"] or r["text_ar"]) for r in d["results"][:2])


def test_hadith_and_narrator_endpoints(client):
    if not _ready(client):
        pytest.skip("base non ingérée")
    h = client.get("/hadiths/bukhari/1").json()
    assert h["number"] == "1" and h["chains"]
    linked = [l for l in h["chains"][0]["links"] if l["narrator"]]
    assert linked, "aucun narrateur lié sur Bukhari n°1"
    n = client.get(f"/narrator/{linked[0]['narrator']['id']}").json()
    assert n["name"] and "grade_label_fr" in n
