"""Ré-extrait les maillons d'isnad de tous les hadiths (sans modifier les ids des hadiths,
donc sans reconstruire les index). À lancer après une évolution du parseur, puis link_narrators."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, insert, select  # noqa: E402

from hadith_bot.db import engine  # noqa: E402
from hadith_bot.isnad import parse_isnad  # noqa: E402
from hadith_bot.models import Hadith, IsnadLink  # noqa: E402


def main() -> None:
    with engine.begin() as conn:
        rows = conn.execute(select(Hadith.id, Hadith.isnad_ar, Hadith.matn_ar)).all()
        conn.execute(delete(IsnadLink))
        batch = []
        for hid, isnad, matn in rows:
            for ci, chain in enumerate(parse_isnad(isnad, matn)):
                for link in chain.links:
                    for l in [link, *link.alternatives]:
                        batch.append(dict(hadith_id=hid, chain_no=ci, position=link.position, name_as_written=l.name, name_norm=l.name_norm,
                                          transmission_term=l.term, transmission_mode=l.mode, is_relative=l.is_relative))
            if len(batch) >= 5000:
                conn.execute(insert(IsnadLink), batch)
                batch = []
        if batch:
            conn.execute(insert(IsnadLink), batch)
    print(f"{len(rows)} hadiths ré-analysés")


if __name__ == "__main__":
    main()
