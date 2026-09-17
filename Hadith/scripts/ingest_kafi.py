"""Charge al-Kāfī (ThaqalaynAPI : 8 volumes, arabe + traduction Sarwar + gradations de Majlisī) dans la base,
avec extraction des isnads par le parseur imamite."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select  # noqa: E402

from hadith_bot.arabic import strip_tashkil  # noqa: E402
from hadith_bot.config import settings  # noqa: E402
from hadith_bot.db import init_db, session_scope  # noqa: E402
from hadith_bot.isnad_shia import parse_isnad_shia  # noqa: E402
from hadith_bot.models import Collection, Hadith, IsnadLink  # noqa: E402

RAW = settings.raw_dir / "shia"
_NUM = re.compile(r"^\s*\d+\s*[-ـ–]?\s*")


def _grade(txt: str | None) -> str | None:
    t = (txt or "").strip()
    return t or None


def main() -> None:
    init_db()
    with session_scope() as s:
        coll = s.scalar(select(Collection).where(Collection.slug == "kafi"))
        if coll is None:
            coll = Collection(slug="kafi", tradition="shia", name_ar="الكافي", name_fr="al-Kāfī", name_en="Al-Kafi")
            s.add(coll)
            s.flush()
        else:
            ids = [h.id for h in s.scalars(select(Hadith).where(Hadith.collection_id == coll.id))]
            if ids:
                s.execute(delete(IsnadLink).where(IsnadLink.hadith_id.in_(ids)))
                s.execute(delete(Hadith).where(Hadith.id.in_(ids)))
                s.flush()
        n = 0
        for v in range(1, 9):
            rows = json.load(open(RAW / f"kafi_v{v}.json", encoding="utf-8"))
            prev_links = None
            for r in rows:
                ar = (r.get("arabicText") or "").strip()
                if not ar:
                    continue
                chains, matn = parse_isnad_shia(ar, prev_links)
                links = chains[0].links if chains else []
                isnad_txt = chains[0].raw if chains else None
                g = r.get("gradingsFull") or []
                maj = next((x for x in g if "Majlisi" in str((x.get("author") or {}).get("name_en"))), None)
                h = Hadith(
                    collection_id=coll.id,
                    hadith_number=f"{v}:{r.get('id')}",
                    chapter_number=r.get("categoryId"),
                    chapter_ar=None,
                    chapter_en=r.get("category"),
                    section_number=r.get("chapterInCategoryId"),
                    section_ar=None,
                    section_en=r.get("chapter"),
                    text_ar=_NUM.sub("", ar),
                    isnad_ar=isnad_txt,
                    matn_ar=matn or None,
                    text_en=(r.get("englishText") or "").strip() or None,
                    isnad_en=(r.get("thaqalaynSanad") or "").strip() or None,
                    matn_en=(r.get("thaqalaynMatn") or "").strip() or None,
                    grade_ar=_grade(r.get("majlisiGrading")),
                    grade_en=None,
                    comment_ar=_grade(r.get("behbudiGrading")),
                    source="ThaqalaynAPI",
                    meta={
                        "volume": v, "number": r.get("id"), "url": r.get("URL"),
                        "majlisi_ref": (maj or {}).get("reference_en"),
                        "behbudi": _grade(r.get("behbudiGrading")), "mohseni": _grade(r.get("mohseniGrading")),
                        "translator": r.get("translator"),
                    },
                )
                s.add(h)
                s.flush()
                for link in links:
                    for l in [link, *link.alternatives]:
                        s.add(IsnadLink(hadith_id=h.id, chain_no=0, position=link.position, name_as_written=l.name, name_norm=l.name_norm,
                                        transmission_term=l.term, transmission_mode=l.mode, is_relative=l.is_relative, kind=l.kind))
                prev_links = links if links else prev_links
                n += 1
            s.commit()
            print(f"  volume {v}: {len(rows)} enregistrements")
        print(f"al-Kāfī : {n} hadiths")


if __name__ == "__main__":
    main()
