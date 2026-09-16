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
    existing = set()
    got = col.get(include=[])
    existing.update(got["ids"])
    print(f"index: {len(existing)} passages déjà présents")
    with SessionLocal() as s:
        q = select(Hadith, Collection.slug, Collection.name_fr).join(Collection)
        if slugs:
            q = q.where(Collection.slug.in_(slugs))
        rows = s.execute(q).all()
    todo = []
    for h, slug, name in rows:
        for j, (lang, txt) in enumerate(passages(h.matn_ar, h.matn_en, h.text_ar)):
            pid = f"h{h.id}:{lang}:{j}"
            if pid not in existing:
                todo.append((pid, txt, {"hadith_id": h.id, "lang": lang, "collection": slug, "collection_name": name, "number": h.hadith_number, "grade": h.grade_ar or ""}))
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
