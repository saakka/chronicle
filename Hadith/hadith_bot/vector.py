"""Index vectoriel ChromaDB + embeddings multilingues (arabe / français / anglais)."""
from __future__ import annotations

from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings

from .config import settings


@lru_cache(maxsize=1)
def embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def _is_e5() -> bool:
    return "e5" in settings.embedding_model.lower()


def embed_passages(texts: list[str]) -> list[list[float]]:
    prefix = "passage: " if _is_e5() else ""
    return embedder().encode([prefix + t for t in texts], normalize_embeddings=True, batch_size=64, show_progress_bar=False).tolist()


def embed_queries(texts: list[str]) -> list[list[float]]:
    prefix = "query: " if _is_e5() else ""
    return embedder().encode([prefix + t for t in texts], normalize_embeddings=True, show_progress_bar=False).tolist()


@lru_cache(maxsize=1)
def client() -> chromadb.ClientAPI:
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.chroma_dir), settings=ChromaSettings(anonymized_telemetry=False))


def collection():
    return client().get_or_create_collection(settings.chroma_collection, metadata={"hnsw:space": "cosine"})


def _chunks(text: str, size: int = 110, overlap: int = 25) -> list[str]:
    words = text.split()
    if len(words) <= size:
        return [text] if words else []
    out, i = [], 0
    while i < len(words):
        out.append(" ".join(words[i : i + size]))
        if i + size >= len(words):
            break
        i += size - overlap
    return out


def passages(matn_ar: str | None, matn_en: str | None, text_ar: str | None) -> list[tuple[str, str]]:
    """Passages indexés : (langue, texte). Arabe (sans tashkil) et anglais séparés, découpés en
    segments courts pour éviter que les longs hadiths n'attirent toutes les requêtes."""
    from .arabic import strip_tashkil

    out: list[tuple[str, str]] = []
    ar = strip_tashkil(matn_ar or text_ar or "").strip()
    en = (matn_en or "").strip()
    out += [("ar", c) for c in _chunks(ar)]
    out += [("en", c) for c in _chunks(en)]
    return out


def search(queries: list[str], k: int = 10, where: dict | None = None) -> list[dict]:
    """Recherche par similarité ; plusieurs formulations et plusieurs passages par hadith fusionnés
    par Reciprocal Rank Fusion (clé = hadith)."""
    col = collection()
    embs = embed_queries(queries)
    fused: dict[int, float] = {}
    meta: dict[int, dict] = {}
    for emb in embs:
        res = col.query(query_embeddings=[emb], n_results=max(k * 6, 40), where=where, include=["metadatas", "distances"])
        seen: set[int] = set()
        rank = 0
        for md, dist in zip(res["metadatas"][0], res["distances"][0]):
            hid = int(md["hadith_id"])
            if hid in seen:
                continue
            seen.add(hid)
            fused[hid] = fused.get(hid, 0.0) + 1.0 / (60 + rank)
            if hid not in meta or dist < meta[hid]["distance"]:
                meta[hid] = {**md, "distance": dist}
            rank += 1
    ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return [{"id": f"h{i}", "score": sc, **meta[i]} for i, sc in ranked]
