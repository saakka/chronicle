"""Construit / met à jour l'index vectoriel des hadiths (ChromaDB)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from hadith_bot.db import SessionLocal  # noqa: E402
from hadith_bot.models import Collection, Hadith  # noqa: E402
from hadith_bot.vector import collection, embed_passages, passages  # noqa: E402


def main(slugs: list[str] | None = None, batch: int = 256) -> None:
    col = collection()
    # lecture paginée (une lecture globale dépasse la limite de variables SQLite du backend Chroma)
    ids_all, metas_all, off = [], [], 0
    while True:
        page = col.get(include=["metadatas"], limit=2000, offset=off)
        if not page["ids"]:
            break
        ids_all += page["ids"]
        metas_all += page["metadatas"]
        off += len(page["ids"])
    existing = set(ids_all)
    print(f"index: {len(existing)} passages déjà présents")
    # rattrapage : passages indexés avant l'ajout de la tradition -> sunni
    missing = [(i, m) for i, m in zip(ids_all, metas_all) if "tradition" not in (m or {})]
    for i in range(0, len(missing), 100):  # limite SQLite de variables dans Chroma (999)
        chunk = missing[i : i + 100]
        col.update(ids=[x for x, _ in chunk], metadatas=[{**(m or {}), "tradition": "sunni"} for _, m in chunk])
    if missing:
        print(f"  {len(missing)} passages marqués tradition=sunni")
    with SessionLocal() as s:
        q = select(Hadith, Collection.slug, Collection.name_fr, Collection.tradition).join(Collection)
        if slugs:
            q = q.where(Collection.slug.in_(slugs))
        rows = s.execute(q).all()
    todo = []
    for h, slug, name, trad in rows:
        for j, (lang, txt) in enumerate(passages(h.matn_ar, h.matn_en, h.text_ar)):
            pid = f"h{h.id}:{lang}:{j}"
            if pid not in existing:
                todo.append((pid, txt, {"hadith_id": h.id, "lang": lang, "collection": slug, "collection_name": name, "number": h.hadith_number, "grade": h.grade_ar or "", "tradition": trad or "sunni"}))
    print(f"{len(todo)} passages à indexer")
    for i in range(0, len(todo), batch):
        chunk = todo[i : i + batch]
        embs = embed_passages([t for _, t, _ in chunk])
        col.add(ids=[p for p, _, _ in chunk], embeddings=embs, documents=[t[:2000] for _, t, _ in chunk], metadatas=[m for _, _, m in chunk])
        if (i // batch) % 10 == 0:
            print(f"  {min(i + batch, len(todo))}/{len(todo)}")
    print("total indexé :", col.count())


if __name__ == "__main__":
    main(sys.argv[1:] or None)
