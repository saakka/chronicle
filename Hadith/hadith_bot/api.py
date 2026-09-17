"""API FastAPI : /ask (pipeline complet), /hadith/{id}, /narrator/{id}, /narrators/search, interface web."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .arabic import normalize_name
from .config import settings
from .db import get_session, init_db
from .models import Hadith, IsnadLink, Narrator, NarratorName
from .retrieval import ask, hadith_dict, hadith_report, load_hadiths, narrator_dict
from . import vector

log = logging.getLogger("hadith_bot")
STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:  # pré-chauffe l'encodeur (évite la latence à la première requête)
        vector.embedder()
    except Exception as e:  # pragma: no cover
        log.warning("embedder non chargé : %s", e)
    if settings.llm_backend == "local":
        from . import local_llm

        if local_llm.available():
            local_llm.warm_up()
    yield


app = FastAPI(title="Bot Hadiths & 'Ilm al-Rijal", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    k: int = Field(default=settings.top_k, ge=1, le=30)
    use_llm: bool = True
    collections: list[str] | None = None
    tradition: str = Field(default="sunni", pattern="^(sunni|shia|both)$")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health(s: Session = Depends(get_session)):
    from .retrieval import _local_available

    if settings.llm_backend == "local":
        available = _local_available
    elif settings.llm_backend == "anthropic":
        from .llm import available
    else:
        def available() -> bool:
            return False

    from .models import Collection

    per_trad = {t: {"hadiths": hc, "narrators": 0} for t, hc in s.execute(select(Collection.tradition, func.count(Hadith.id)).join(Hadith).group_by(Collection.tradition))}
    for t, nc in s.execute(select(Narrator.tradition, func.count(Narrator.id)).group_by(Narrator.tradition)):
        per_trad.setdefault(t, {"hadiths": 0, "narrators": 0})["narrators"] = nc
    return {
        "llm_backend": settings.llm_backend,
        "local_model": settings.local_model if settings.llm_backend == "local" else None,
        "status": "ok",
        "traditions": per_trad,
        "hadiths": s.scalar(select(func.count(Hadith.id))),
        "narrators": s.scalar(select(func.count(Narrator.id))),
        "isnad_links": s.scalar(select(func.count(IsnadLink.id))),
        "linked_links": s.scalar(select(func.count(IsnadLink.id)).where(IsnadLink.narrator_id.is_not(None))),
        "vectors": vector.collection().count(),
        "llm": available(),
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
    }


@app.post("/ask")
def ask_endpoint(req: AskRequest, s: Session = Depends(get_session)):
    return ask(s, req.question, k=req.k, use_llm=req.use_llm, collections=req.collections, tradition=req.tradition)


@app.get("/report/{hadith_id}", include_in_schema=False)
def report_page(hadith_id: int):
    return FileResponse(STATIC / "report.html")


@app.get("/hadith/{hadith_id}/report")
def get_hadith_report(hadith_id: int, use_llm: bool = True, s: Session = Depends(get_session)):
    r = hadith_report(s, hadith_id, use_llm=use_llm)
    if r is None:
        raise HTTPException(404, "hadith introuvable")
    return r


@app.get("/hadith/{hadith_id}")
def get_hadith(hadith_id: int, s: Session = Depends(get_session)):
    h = load_hadiths(s, [hadith_id]).get(hadith_id)
    if h is None:
        raise HTTPException(404, "hadith introuvable")
    return hadith_dict(h)


@app.get("/hadiths/{collection}/{number}")
def get_hadith_by_ref(collection: str, number: str, s: Session = Depends(get_session)):
    from .models import Collection

    h = s.scalar(select(Hadith).join(Collection).where(Collection.slug == collection, Hadith.hadith_number == number))
    if h is None:
        raise HTTPException(404, "hadith introuvable")
    return hadith_dict(load_hadiths(s, [h.id])[h.id])


@app.get("/narrator/{narrator_id}")
def get_narrator(narrator_id: int, s: Session = Depends(get_session)):
    n = s.scalar(select(Narrator).where(Narrator.id == narrator_id).options(selectinload(Narrator.opinions), selectinload(Narrator.names)))
    if n is None:
        raise HTTPException(404, "narrateur introuvable")
    d = narrator_dict(n, with_opinions=True)
    d["names"] = sorted({x.name_ar for x in n.names})
    d["hadith_count"] = s.scalar(select(func.count(func.distinct(IsnadLink.hadith_id))).where(IsnadLink.narrator_id == n.id))
    # passerelle factuelle : même nom dans l'autre tradition (statuts affichés côte à côte, sans arbitrage)
    other = "shia" if n.tradition == "sunni" else "sunni"
    ids = list(dict.fromkeys(s.scalars(select(NarratorName.narrator_id).join(Narrator).where(Narrator.tradition == other, NarratorName.name_norm == n.name_norm)).all()))[:3]
    d["counterparts"] = [narrator_dict(x) for x in s.scalars(select(Narrator).where(Narrator.id.in_(ids))).all()] if ids else []
    return d


@app.get("/narrators/search")
def search_narrators(q: str = Query(min_length=2), limit: int = Query(20, le=100), s: Session = Depends(get_session)):
    nn = normalize_name(q)
    ids = s.scalars(
        select(NarratorName.narrator_id).where(or_(NarratorName.name_norm == nn, NarratorName.name_norm.like(f"{nn}%"))).limit(limit * 3)
    ).all()
    ids = list(dict.fromkeys(ids))[:limit]
    if not ids:
        return []
    rows = s.scalars(select(Narrator).where(Narrator.id.in_(ids))).all()
    return [narrator_dict(n) for n in rows]


@app.get("/narrator/{narrator_id}/hadiths")
def narrator_hadiths(narrator_id: int, limit: int = Query(20, le=100), s: Session = Depends(get_session)):
    ids = s.scalars(select(func.distinct(IsnadLink.hadith_id)).where(IsnadLink.narrator_id == narrator_id).limit(limit)).all()
    hm = load_hadiths(s, list(ids))
    return [hadith_dict(h, full=False) for h in hm.values()]
