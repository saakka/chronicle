"""Ré-extrait les maillons d'isnad de tous les hadiths (sans modifier les ids des hadiths,
donc sans reconstruire les index). À lancer après une évolution du parseur, puis link_narrators."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, insert, select  # noqa: E402

from hadith_bot.db import engine  # noqa: E402
from hadith_bot.isnad import parse_isnad  # noqa: E402
from hadith_bot.isnad_shia import parse_isnad_shia  # noqa: E402
from hadith_bot.models import Collection, Hadith, IsnadLink  # noqa: E402


def _rows(chains, hid):
    out = []
    for ci, chain in enumerate(chains):
        for link in chain.links:
            for l in [link, *link.alternatives]:
                out.append(dict(hadith_id=hid, chain_no=ci, position=link.position, name_as_written=l.name, name_norm=l.name_norm,
                                transmission_term=l.term, transmission_mode=l.mode, is_relative=l.is_relative, kind=getattr(l, "kind", "normal")))
    return out


def main(tradition: str | None = None) -> None:
    with engine.begin() as conn:
        q = select(Hadith.id, Hadith.isnad_ar, Hadith.matn_ar, Hadith.text_ar, Collection.tradition, Hadith.hadith_number).join(Collection)
        if tradition:
            q = q.where(Collection.tradition == tradition)
        rows = conn.execute(q.order_by(Collection.id, Hadith.id)).all()
        ids = [r[0] for r in rows]
        for i in range(0, len(ids), 500):
            conn.execute(delete(IsnadLink).where(IsnadLink.hadith_id.in_(ids[i : i + 500])))
        batch, prev_links, n = [], None, 0
        for hid, isnad, matn, text_ar, trad, _num in rows:
            if trad == "shia":
                chains, matn_new = parse_isnad_shia(text_ar, prev_links)
                if chains and chains[0].links:
                    prev_links = chains[0].links
                    conn.execute(Hadith.__table__.update().where(Hadith.id == hid).values(isnad_ar=chains[0].raw, matn_ar=matn_new or None))
            else:
                chains = parse_isnad(isnad, matn)
            batch.extend(_rows(chains, hid))
            n += 1
            if len(batch) >= 5000:
                conn.execute(insert(IsnadLink), batch)
                batch = []
        if batch:
            conn.execute(insert(IsnadLink), batch)
    print(f"{n} hadiths ré-analysés")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
