"""Base des narrateurs imamites (tradition « shia ») :
  - al-Jawāhirī, al-Mufīd min Muʿjam rijāl al-ḥadīth (résumé de Khūʾī : un verdict par narrateur) -> notices principales
  - Najāshī, Ṭūsī (Rijāl), ʿAllāma Ḥillī (Khulāṣa) -> avis sourcés rattachés par le nom
  - entrées virtuelles : les Infaillibles (terminaison des chaînes) et la ʿidda d'al-Kulaynī."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, insert, select  # noqa: E402

from hadith_bot.arabic import normalize_name  # noqa: E402
from hadith_bot.config import settings  # noqa: E402
from hadith_bot.db import engine, init_db, session_scope  # noqa: E402
from hadith_bot.grading_shia import classify_shia  # noqa: E402
from hadith_bot.models import Narrator, NarratorName, NarratorOpinion  # noqa: E402

RAW = settings.raw_dir / "shia"
_PAGE = re.compile(r"\s*(ms\d+|PageV\d+P\d+)\s*")
_ENTRY = re.compile(r"^# *(?:\(\d+\) *)?(\d+) *[-–] *(\d+) *[-–] *(\d+) *[-–] *(.+)$")  # « # (1) 2638 - 2637 - 2645 - Nom: ... »
_CLASSIC = re.compile(r"^### \$ *(\[\])? *(\d+) *[-–] *(.+)$")

IMAMS = [
    ("النبي محمد صلى الله عليه وآله", ["رسول الله", "النبي", "محمد رسول الله", "نبي الله"]),
    ("أمير المؤمنين علي بن أبي طالب", ["امير المومنين", "علي بن ابي طالب", "علي عليه السلام"]),
    ("الحسن بن علي المجتبى", ["الحسن بن علي", "ابي محمد الحسن"]),
    ("الحسين بن علي سيد الشهداء", ["الحسين بن علي", "ابي عبدالله الحسين"]),
    ("علي بن الحسين زين العابدين", ["علي بن الحسين", "زين العابدين", "السجاد"]),
    ("محمد بن علي الباقر", ["ابي جعفر", "ابو جعفر", "الباقر", "ابي جعفر الباقر", "محمد بن علي الباقر", "ابي جعفر محمد بن علي"]),
    ("جعفر بن محمد الصادق", ["ابي عبدالله", "ابو عبدالله", "الصادق", "جعفر بن محمد", "ابي عبدالله جعفر بن محمد", "ابي عبدالله الصادق"]),
    ("موسى بن جعفر الكاظم", ["ابي الحسن موسي", "ابي ابراهيم", "العبد الصالح", "ابي الحسن الاول", "ابي الحسن الماضي", "الكاظم", "موسي بن جعفر", "ابي الحسن موسي بن جعفر"]),
    ("علي بن موسى الرضا", ["ابي الحسن الرضا", "الرضا", "ابي الحسن الثاني", "علي بن موسي", "ابو الحسن الرضا"]),
    ("محمد بن علي الجواد", ["ابي جعفر الثاني", "الجواد", "ابو جعفر الثاني", "ابي جعفر محمد بن علي الرضا"]),
    ("علي بن محمد الهادي", ["ابي الحسن الثالث", "الهادي", "ابي الحسن العسكري", "ابو الحسن الثالث", "ابي الحسن صاحب العسكر"]),
    ("الحسن بن علي العسكري", ["ابي محمد", "ابو محمد", "العسكري", "ابي محمد العسكري", "ابي محمد الحسن بن علي"]),
    ("صاحب الزمان المهدي", ["صاحب الزمان", "القايم", "الحجه", "المهدي"]),
    ("أبو الحسن (الكاظم، الرضا ou الهادي, non précisé)", ["ابي الحسن", "ابو الحسن"]),
    ("أحدهما (الباقر أو الصادق)", ["احدهما", "عن احدهما"]),
]
# formes courtes usuelles d'al-Kāfī -> narrateur visé (usage constant des usūlīs ; les cas ambigus sont laissés au contexte)
SHORT_FORMS = {
    "ابن فضال": "الحسن بن علي بن فضال",
    "حريز": "حريز بن عبد الله السجستاني",
    "ابن محبوب": "الحسن بن محبوب",
    "ابن أبي عمير": "محمد بن أبي عمير",
    "يونس": "يونس بن عبد الرحمن",
    "أبان": "أبان بن عثمان",
    "زرارة": "زرارة بن أعين",
    "جميل": "جميل بن دراج",
    "صفوان": "صفوان بن يحيى",
    "ابن أبي نجران": "عبد الرحمن بن أبي نجران",
    "ابن مسكان": "عبد الله بن مسكان",
    "ابن بكير": "عبد الله بن بكير",
    "ابن رئاب": "علي بن رئاب",
    "ابن أذينة": "عمر بن أذينة",
    "أبو أيوب": "أبو أيوب الخزاز",
    "أبو المغراء": "حميد بن المثنى",
    "أبي المغراء": "حميد بن المثنى",
    "فضالة": "فضالة بن أيوب",
    "معاوية بن عمار": "معاوية بن عمار",
    "البرقي": "أحمد بن محمد بن خالد البرقي",
    "الحسين بن سعيد": "الحسين بن سعيد بن حماد",
    "النضر بن سويد": "النضر بن سويد",
    "ابن سماعة": "الحسن بن محمد بن سماعة",
    "ابن أبي يعفور": "عبد الله بن أبي يعفور",
    "أبو ولاد": "حفص بن سالم",
}
IDDA_NOTE = ("Groupe de maîtres d'al-Kulaynī, composition documentée par al-Najāshī et al-ʿAllāma : "
             "auprès d'Aḥmad b. Muḥammad b. ʿĪsā : Muḥammad b. Yaḥyā al-ʿAṭṭār, ʿAlī b. Mūsā al-Kumaydhānī, Dāwūd b. Kūra, Aḥmad b. Idrīs, ʿAlī b. Ibrāhīm ; "
             "auprès d'Aḥmad b. Muḥammad al-Barqī : ʿAlī b. Ibrāhīm, ʿAlī b. Muḥammad b. ʿAbd Allāh b. Udhayna, Aḥmad b. ʿAbd Allāh b. Umayya, ʿAlī b. al-Ḥasan ; "
             "auprès de Sahl b. Ziyād : ʿAlī b. Muḥammad b. ʿAllān, Muḥammad b. Abī ʿAbd Allāh, Muḥammad b. al-Ḥasan, Muḥammad b. ʿAqīl al-Kulaynī. "
             "Tenu pour fiable par al-Khūʾī et la majorité des usūlīs.")


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", _PAGE.sub(" ", t)).strip()


def parse_jawahiri(path: Path) -> list[dict]:
    entries: list[dict] = []
    cur = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = _ENTRY.match(line)
        if m:
            if cur:
                entries.append(cur)
            body = _clean(m.group(4))
            if ":" in body:
                name, rest = body.split(":", 1)
            else:
                name, rest = body, ""
            cur = {"num": int(m.group(1)), "name": name.strip(" .:-"), "text": rest.strip()}
        elif cur is not None and line.startswith("~~"):
            cur["text"] += " " + _clean(line[2:])
        elif cur is not None and line.startswith("# ") and not line.startswith("# PageV"):
            cur["text"] += " " + _clean(line[2:])
    if cur:
        entries.append(cur)
    # « name: بن فلان ... - ثقة » : le début du texte prolonge la nasab
    for e in entries:
        t = e["text"]
        if t.startswith("بن ") or t.startswith("ابن "):
            first = re.split(r"\s-\s", t, 1)
            e["name"] = (e["name"] + " " + first[0]).strip()
            e["text"] = first[1] if len(first) > 1 else ""
        e["name"] = re.sub(r'\s*"[^"]*"\s*', " ", e["name"]).strip()
    return entries


def parse_classic(path: Path) -> list[dict]:
    entries: list[dict] = []
    cur = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = _CLASSIC.match(line)
        if m:
            if cur:
                entries.append(cur)
            head = _clean(m.group(3))
            name = re.split(r"\s-\s|،|,", head, 1)[0].strip(" .:-")
            cur = {"num": int(m.group(2)), "name": name, "text": head}
        elif line.startswith("###"):
            if cur:
                entries.append(cur)
            cur = None
        elif cur is not None and (line.startswith("~~") or line.startswith("# ")):
            cur["text"] += " " + _clean(line.lstrip("~#"))
    if cur:
        entries.append(cur)
    return entries


def main() -> None:
    init_db()
    with engine.begin() as conn:
        ids = [r[0] for r in conn.execute(select(Narrator.id).where(Narrator.tradition == "shia")).all()]
        if ids:
            conn.execute(delete(NarratorOpinion).where(NarratorOpinion.narrator_id.in_(ids)))
            conn.execute(delete(NarratorName).where(NarratorName.narrator_id.in_(ids)))
            conn.execute(delete(Narrator).where(Narrator.id.in_(ids)))
    jaw = parse_jawahiri(RAW / "jawahiri_mufid.txt")
    print(f"al-Jawāhirī : {len(jaw)} notices")
    rows, names = [], []
    for k, e in enumerate(jaw):
        e["name"] = re.split(r"\s(من اصحاب|من أصحاب|روى|قال|كان|له |مولى)\s", e["name"], 1)[0].strip(" .:-،")
        if not e["name"] or len(e["name"]) < 2:
            continue
        cat, rank = classify_shia(e["text"])
        ext = f"jawahiri:{e['num']}:{k}"
        rows.append(dict(
            external_id=ext, tradition="shia", name_ar=e["name"], name_norm=normalize_name(e["name"]), is_companion=False,
            grade_category=cat, grade_rank=rank, grade_ibn_hajar=None, grade_dhahabi=None,
            sources={"jawahiri": {"grade": e["text"][:160], "entry": e["num"]}},
            extra={"grade_text": e["text"][:400], "origin": "jawahiri", "teachers": [], "students": [], "merged_ids": [],
                   "narrations": int(m.group(1)) if (m := re.search(r"روى (\d+) رواي", e["text"])) else 0,
                   "verdict_source": "al-Mufīd min Muʿjam rijāl al-ḥadīth (Khūʾī résumé)"},
        ))
        variants = {e["name"]}
        t = normalize_name(e["name"]).split()  # « عبد الرحمن » compte pour un seul jeton après normalisation
        # préfixes à chaque « بن » : « أحمد بن محمد », « أحمد بن محمد بن عيسى », ...
        for k2 in range(3, len(t) + 1, 2):
            if t[k2 - 2] == "بن":
                variants.add(" ".join(t[:k2]))
        nn_full = normalize_name(e["name"])
        for short, full in SHORT_FORMS.items():
            head = " ".join(normalize_name(full).split()[:3])  # « حريز بن عبدالله » suffit
            if nn_full == head or nn_full.startswith(head + " ") or nn_full == normalize_name(full):
                variants.add(short)
        names.append((ext, variants))
    # entrées virtuelles
    for i, (name, variants) in enumerate(IMAMS):
        rows.append(dict(external_id=f"imam:{i}", tradition="shia", name_ar=name, name_norm=normalize_name(name), is_companion=False,
                         grade_category="imam", grade_rank=6, grade_ibn_hajar=None, grade_dhahabi=None, sources={},
                         extra={"grade_text": "معصوم", "origin": "virtual", "teachers": [], "students": [], "merged_ids": []}))
        names.append((f"imam:{i}", set(variants) | {name}))
    rows.append(dict(external_id="idda:kulayni", tradition="shia", name_ar="عدة من أصحابنا (مشايخ الكليني)", name_norm=normalize_name("عدة من أصحابنا"), is_companion=False,
                     grade_category="group", grade_rank=5, grade_ibn_hajar=None, grade_dhahabi=None, sources={"najashi": {"grade": "تركيب العدة"}},
                     extra={"grade_text": IDDA_NOTE, "origin": "virtual", "teachers": [], "students": [], "merged_ids": []}))
    names.append(("idda:kulayni", {"عدة من أصحابنا", "عده من اصحابنا"}))
    with engine.begin() as conn:
        for i in range(0, len(rows), 2000):
            conn.execute(insert(Narrator), rows[i : i + 2000])
        ids = dict(conn.execute(select(Narrator.external_id, Narrator.id).where(Narrator.tradition == "shia")).all())
        name_rows = []
        for ext, variants in names:
            nid = ids[ext]
            seen = set()
            for v in variants:
                nn = normalize_name(v)
                if nn and nn not in seen:
                    seen.add(nn)
                    name_rows.append(dict(narrator_id=nid, name_ar=v, name_norm=nn))
        conn.execute(insert(NarratorName), name_rows)
    print(f"{len(rows)} narrateurs chiites, {len(name_rows)} variantes")
    # avis classiques rattachés par le nom
    sources = [("najashi_rijal.txt", "النجاشي", "رجال النجاشي"), ("tusi_rijal.txt", "الشيخ الطوسي", "رجال الطوسي"), ("hilli_khulasa.txt", "العلامة الحلي", "خلاصة الأقوال")]
    with session_scope() as s:
        idx: dict[str, list[int]] = {}
        for nn, nid in s.execute(select(NarratorName.name_norm, NarratorName.narrator_id).join(Narrator).where(Narrator.tradition == "shia")):
            idx.setdefault(nn, []).append(nid)
        for fname, critic, book in sources:
            ents = parse_classic(RAW / fname)
            linked = 0
            for e in ents:
                nn = normalize_name(e["name"])
                cands = idx.get(nn) or idx.get(" ".join(nn.split()[:3])) or []
                if not cands:
                    continue
                cat, _ = classify_shia(e["text"])
                kind = "tadil" if cat in ("thiqa", "muwaththaq", "mamduh") else "jarh" if cat in ("daif", "kadhdhab", "majhul") else "unknown"
                s.add(NarratorOpinion(narrator_id=cands[0], critic=critic, opinion=e["text"][:500], kind=kind, source_book=f"{book} n°{e['num']}"))
                linked += 1
            print(f"{book} : {len(ents)} notices, {linked} rattachées")


if __name__ == "__main__":
    main()
