"""Recherche lexicale (BM25) complémentaire à la recherche vectorielle.

SQLite : table virtuelle FTS5 sur le texte normalisé (arabe sans tashkil + anglais).
PostgreSQL : tsvector « simple » sur la même colonne (index GIN)."""
from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from .arabic import normalize, strip_tashkil
from .db import engine

IS_SQLITE = engine.dialect.name == "sqlite"


def doc_text(matn_ar: str | None, matn_en: str | None, text_ar: str | None, chapter_ar: str | None = None, section_ar: str | None = None) -> str:
    ar = normalize(matn_ar or text_ar or "")
    en = re.sub(r"[^\w\s']", " ", (matn_en or "").lower())
    extra = normalize(f"{chapter_ar or ''} {section_ar or ''}")
    return f"{ar}\n{en}\n{extra}".strip()


def build(session: Session) -> int:
    rows = session.execute(text(
        "SELECT h.id, h.matn_ar, h.matn_en, h.text_ar, h.chapter_ar, h.section_ar, c.tradition FROM hadiths h JOIN collections c ON c.id = h.collection_id"
    )).all()
    params = [{"id": r[0], "body": doc_text(r[1], r[2], r[3], r[4], r[5]), "trad": r[6] or "sunni"} for r in rows]
    session.execute(text("DROP TABLE IF EXISTS hadith_fts"))
    if IS_SQLITE:
        session.execute(text("CREATE VIRTUAL TABLE hadith_fts USING fts5(hadith_id UNINDEXED, tradition UNINDEXED, body, tokenize='porter unicode61 remove_diacritics 2')"))
    else:
        session.execute(text("CREATE TABLE hadith_fts (hadith_id INTEGER PRIMARY KEY, tradition TEXT, body TEXT, tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', body)) STORED)"))
        session.execute(text("CREATE INDEX hadith_fts_tsv ON hadith_fts USING GIN (tsv)"))
    session.execute(text("INSERT INTO hadith_fts(hadith_id, tradition, body) VALUES (:id, :trad, :body)"), params)
    session.commit()
    return len(rows)


_TOKEN = re.compile(r"[\w']+")
# mots vides (fr/en/ar) ignorés pour la couverture des termes
STOP = set("""le la les l un une des du de d et ou en dans sur pour par avec sans au aux ce cette ces qui que quoi dont est sont a à il elle on nous vous ils
the a an of in on for to and or is are was were be by with about from as at that this these those what which who whom how why when where do does did can could should would
في من على عن الى إلى ان أن و او أو ثم مع هذا هذه ذلك التي الذي ما لا لم لن قد كان كانت هو هي هل كيف متى اين أين ماذا لماذا يا عند حتى بين""".split())


def content_terms(q: str) -> list[str]:
    return [t for t in _terms(q) if t not in STOP and len(t) > 1]


def coverage(session: Session, query: str, hadith_ids: list[int]) -> dict[int, tuple[float, bool]]:
    """Pour chaque hadith candidat : (part pondérée IDF des termes de la question présents,
    présence du terme le plus rare). 1.0 = tous les termes y figurent ; 0 = aucun."""
    toks = content_terms(query)
    if not toks or not hadith_ids:
        return {h: (0.0, False) for h in hadith_ids}
    import math

    try:
        n_docs = session.execute(text("SELECT count(*) FROM hadith_fts")).scalar() or 1
        ids_sql = ",".join(str(int(h)) for h in hadith_ids)
        weights: dict[str, float] = {}
        hits: dict[int, float] = {h: 0.0 for h in hadith_ids}
        present: dict[str, set[int]] = {}
        for t in toks:
            if IS_SQLITE:
                df = session.execute(text("SELECT count(*) FROM hadith_fts WHERE hadith_fts MATCH :m"), {"m": f'"{t}"'}).scalar() or 0
                rows = session.execute(text(f"SELECT hadith_id FROM hadith_fts WHERE hadith_fts MATCH :m AND hadith_id IN ({ids_sql})"), {"m": f'"{t}"'}).all()
            else:
                df = session.execute(text("SELECT count(*) FROM hadith_fts WHERE tsv @@ plainto_tsquery('simple', :q)"), {"q": t}).scalar() or 0
                rows = session.execute(text(f"SELECT hadith_id FROM hadith_fts WHERE tsv @@ plainto_tsquery('simple', :q) AND hadith_id IN ({ids_sql})"), {"q": t}).all()
            w = math.log((n_docs + 1) / (df + 1)) + 0.1
            weights[t] = w
            present[t] = {int(h) for (h,) in rows}
            for h in present[t]:
                hits[h] += w
        total = sum(weights.values()) or 1.0
        rarest = max(weights, key=weights.get)
        return {h: (round(v / total, 3), h in present[rarest]) for h, v in hits.items()}
    except Exception:
        session.rollback()
        return {h: (0.0, False) for h in hadith_ids}


def _terms(q: str) -> list[str]:
    t = normalize(q).lower()
    toks = [w for w in _TOKEN.findall(t) if len(w) > 1]
    return toks[:24]


def _trad_clause(tradition: str | None) -> str:
    return " AND tradition = :trad" if tradition else ""


def search(session: Session, query: str, k: int = 20, tradition: str | None = None) -> list[tuple[int, float]]:
    """Renvoie [(hadith_id, score)] triés du meilleur au moins bon (BM25 en SQLite, ts_rank en PG)."""
    toks = _terms(query)
    if not toks:
        return []
    try:
        if IS_SQLITE:
            match = " OR ".join(f'"{t}"' for t in toks)
            rows = session.execute(
                text(f"SELECT hadith_id, bm25(hadith_fts) AS r FROM hadith_fts WHERE hadith_fts MATCH :m{_trad_clause(tradition)} ORDER BY r LIMIT :k"),
                {"m": match, "k": k, "trad": tradition},
            ).all()
            return [(int(h), float(-r)) for h, r in rows]
        rows = session.execute(
            text(f"SELECT hadith_id, ts_rank(tsv, q) AS r FROM hadith_fts, to_tsquery('simple', :q) q WHERE tsv @@ q{_trad_clause(tradition)} ORDER BY r DESC LIMIT :k"),
            {"q": " | ".join(toks), "k": k, "trad": tradition},
        ).all()
        return [(int(h), float(r)) for h, r in rows]
    except Exception:  # table absente (index non construit) -> pas de composante lexicale
        session.rollback()
        return []


def phrase_search(session: Session, query: str, k: int = 20, tradition: str | None = None) -> list[int]:
    """Hadiths contenant la requête comme expression contiguë (signal fort : « إنما الأعمال بالنيات »)."""
    toks = _terms(query)
    if len(toks) < 2:
        return []
    try:
        if IS_SQLITE:
            phrase = '"' + " ".join(toks) + '"'
            rows = session.execute(
                text(f"SELECT hadith_id FROM hadith_fts WHERE hadith_fts MATCH :m{_trad_clause(tradition)} ORDER BY bm25(hadith_fts) LIMIT :k"), {"m": phrase, "k": k, "trad": tradition}
            ).all()
        else:
            rows = session.execute(
                text(f"SELECT hadith_id FROM hadith_fts WHERE tsv @@ phraseto_tsquery('simple', :q){_trad_clause(tradition)} ORDER BY ts_rank(tsv, phraseto_tsquery('simple', :q)) DESC LIMIT :k"),
                {"q": " ".join(toks), "k": k, "trad": tradition},
            ).all()
        return [int(r[0]) for r in rows]
    except Exception:
        session.rollback()
        return []
