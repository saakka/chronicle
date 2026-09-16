"""Charge le corpus LK (6 recueils, isnad/matn séparés) dans la base SQL et extrait les maillons d'isnad."""
from __future__ import annotations

import csv
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
csv.field_size_limit(10**9)

from sqlalchemy import delete, select  # noqa: E402

from hadith_bot.config import settings  # noqa: E402
from hadith_bot.db import init_db, session_scope  # noqa: E402
from hadith_bot.isnad import parse_isnad  # noqa: E402
from hadith_bot.models import Collection, Hadith, IsnadLink  # noqa: E402

BOOKS = {
    # dossier LK : (slug, arabe, français, anglais)
    "Bukhari": ("bukhari", "صحيح البخاري", "Sahih al-Bukhari", "Sahih al-Bukhari"),
    "Muslim": ("muslim", "صحيح مسلم", "Sahih Muslim", "Sahih Muslim"),
    "AbuDaud": ("abudawud", "سنن أبي داود", "Sunan Abu Dawud", "Sunan Abi Dawud"),
    "Tirmizi": ("tirmidhi", "جامع الترمذي", "Jami' at-Tirmidhi", "Jami` at-Tirmidhi"),
    "Nesai": ("nasai", "سنن النسائي", "Sunan an-Nasa'i", "Sunan an-Nasa'i"),
    "IbnMaja": ("ibnmajah", "سنن ابن ماجه", "Sunan Ibn Majah", "Sunan Ibn Majah"),
}


def _s(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return None if v in ("", "nan", "NaN") else v


def _num(v: str | None) -> str | None:
    v = _s(v)
    if v is None:
        return None
    try:
        f = float(v)
        return str(int(f)) if f.is_integer() else v
    except ValueError:
        return v


def _int(v: str | None) -> int | None:
    v = _num(v)
    try:
        return int(v) if v is not None else None
    except ValueError:
        return None


def main(books: list[str] | None = None) -> None:
    init_db()
    root = settings.raw_dir / "LK-Hadith-Corpus"
    if not root.exists():
        sys.exit(f"corpus introuvable : {root} (lancer scripts/download_data.py)")
    with session_scope() as s:
        for folder, (slug, ar, fr, en) in BOOKS.items():
            if books and slug not in books:
                continue
            coll = s.scalar(select(Collection).where(Collection.slug == slug))
            if coll is None:
                coll = Collection(slug=slug, name_ar=ar, name_fr=fr, name_en=en)
                s.add(coll)
                s.flush()
            else:
                # ré-ingestion : on repart de zéro pour ce recueil
                ids = [h.id for h in s.scalars(select(Hadith).where(Hadith.collection_id == coll.id))]
                if ids:
                    s.execute(delete(IsnadLink).where(IsnadLink.hadith_id.in_(ids)))
                    s.execute(delete(Hadith).where(Hadith.id.in_(ids)))
                    s.flush()
            n = 0
            seen: set[str] = set()
            files = sorted(glob.glob(str(root / folder / "*.csv")), key=lambda p: int(Path(p).stem.replace("Chapter", "") or 0))
            for f in files:
                with open(f, encoding="utf-8", newline="") as fh:
                    for row in csv.DictReader(fh):
                        text_ar = _s(row.get("Arabic_Hadith"))
                        if not text_ar:
                            continue
                        num = _num(row.get("Hadith_number")) or f"{Path(f).stem}-{n}"
                        if num in seen:  # doublons dans certains chapitres -> suffixe
                            k = 2
                            while f"{num}-{k}" in seen:
                                k += 1
                            num = f"{num}-{k}"
                        seen.add(num)
                        h = Hadith(
                            collection_id=coll.id,
                            hadith_number=num,
                            chapter_number=_int(row.get("Chapter_Number")),
                            chapter_ar=_s(row.get("Chapter_Arabic")),
                            chapter_en=_s(row.get("Chapter_English")),
                            section_number=_int(row.get("Section_Number")),
                            section_ar=_s(row.get("Section_Arabic")),
                            section_en=_s(row.get("Section_English")),
                            text_ar=text_ar,
                            isnad_ar=_s(row.get("Arabic_Isnad")),
                            matn_ar=_s(row.get("Arabic_Matn")),
                            text_en=_s(row.get("English_Hadith")),
                            isnad_en=_s(row.get("English_Isnad")),
                            matn_en=_s(row.get("English_Matn")),
                            grade_ar=_s(row.get("Arabic_Grade")),
                            grade_en=_s(row.get("English_Grade")),
                            comment_ar=_s(row.get("Arabic_Comment")),
                        )
                        s.add(h)
                        s.flush()
                        for ci, chain in enumerate(parse_isnad(h.isnad_ar, h.matn_ar)):
                            for link in chain.links:
                                for j, l in enumerate([link, *link.alternatives]):
                                    s.add(
                                        IsnadLink(
                                            hadith_id=h.id,
                                            chain_no=ci,
                                            position=link.position,
                                            name_as_written=l.name,
                                            name_norm=l.name_norm,
                                            transmission_term=l.term,
                                            transmission_mode=l.mode,
                                            is_relative=l.is_relative,
                                        )
                                    )
                        n += 1
                        if n % 2000 == 0:
                            s.flush()
                            print(f"  {slug}: {n}")
            s.commit()
            print(f"{slug}: {n} hadiths")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
