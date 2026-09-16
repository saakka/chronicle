"""Charge la base des narrateurs (Itqan : 115 735 notices issues de 22 ouvrages classiques) et les
avis détaillés de Jarh wa Ta'dil (1 524 narrateurs, avec critique et source) dans la base SQL.

Les notices Itqan contiennent des doublons (même personne importée depuis plusieurs ouvrages) :
on fusionne les profils dont la chaîne « X بن Y بن Z » est identique et dont les dates de décès /
tabaqa sont compatibles, en gardant comme notice principale celle qui a le plus de relations
maîtres/élèves (utile pour désambiguïser les homonymes dans les isnads)."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, insert, select  # noqa: E402

from hadith_bot.arabic import normalize, normalize_name  # noqa: E402
from hadith_bot.config import settings  # noqa: E402
from hadith_bot.db import engine, init_db, session_scope  # noqa: E402
from hadith_bot.grading import CATEGORIES, classify_grade_text  # noqa: E402
from hadith_bot.models import Narrator, NarratorName, NarratorOpinion  # noqa: E402

RIJAL = settings.raw_dir / "itqan" / "app" / "data" / "rijal"
EXTERNAL = settings.raw_dir / "itqan" / "src" / "external_narrators_db.json"

ITQAN_CATEGORY = {
    "companion": "companion", "reliable": "thiqa", "mostly_reliable": "saduq", "weak": "daif",
    "abandoned": "matruk", "fabricator": "kadhdhab", "unknown": "unknown",
}
_COMPANION_TABAQA = re.compile(r"صحاب|له صحبه|لها صحبه|\bالاولي\b")
_COMPANION_TEXT = re.compile(r"صحابي|صحابيه|له صحبه|لها صحبه|من الصحابه|امير المومنين|ام المومنين|له رويه|لها رويه")


def _clean(v) -> str | None:
    if v is None:
        return None
    v = str(v).strip().strip(".").strip()
    return None if v in ("", "-", "nan", "None") else v


def _year(v: str | None) -> int | None:
    v = _clean(v)
    if not v:
        return None
    m = re.search(r"(\d{1,3})\s*هـ", v) or re.search(r"\b(\d{1,3})\b", v)
    return int(m.group(1)) if m else None


def person_key(full_norm: str) -> str | None:
    """Clé de fusion : « X بن Y بن Z » (5 jetons) ; noms plus courts -> clé complète si « X بن Y »."""
    t = full_norm.split()
    if len(t) >= 5 and t[1] == "بن" and t[3] == "بن":
        return " ".join(t[:5])
    if len(t) == 3 and t[1] == "بن":
        return " ".join(t)
    return None


def is_companion(p: dict, file_grade: str) -> bool:
    tab = normalize(p.get("tabaqat") or "")
    g = normalize(p.get("grade_ar") or "")
    if _COMPANION_TABAQA.search(tab) or _COMPANION_TEXT.search(g):
        return True
    if file_grade == "companion":
        cat, _ = classify_grade_text(g)
        if cat and cat != "companion" and tab and not re.search(r"الاولي|الثانيه|صحاب", tab):
            return False  # notice mal classée par la source (formule claire + tabaqa tardive)
        return True
    return False


def build_row(p: dict, file_grade: str) -> tuple[dict, list[str]]:
    full = _clean(p.get("full_name")) or f"narrateur {p['id']}"
    grade_ar = _clean(p.get("grade_ar"))
    inferred = bool(grade_ar and (grade_ar.startswith("استنباط") or grade_ar.startswith("[")))
    auto = bool(grade_ar and "جوامع الكلم" in grade_ar)
    comp = is_companion(p, file_grade)
    if comp:
        cat, rank = "companion", 6
    else:
        cat, rank = (None, None) if inferred else classify_grade_text(grade_ar)
        if cat is None:
            cat = ITQAN_CATEGORY[file_grade]
            rank = CATEGORIES[cat][0]
    sources = p.get("classical_sources") or {}
    prov = p.get("provenance") or {}
    row = dict(
        external_id=f"itqan:{p['id']}",
        name_ar=full,
        name_norm=normalize_name(full),
        kunya=_clean(p.get("kunya")),
        laqab=_clean(p.get("laqab")),
        nasab=_clean(p.get("nasab")),
        tabaqa=_clean(p.get("tabaqat")),
        death_year_h=_year(p.get("death")),
        city=_clean(p.get("city")),
        is_companion=comp,
        grade_ibn_hajar=grade_ar if (grade_ar and not inferred and not auto and "taqrib" in sources) else None,
        grade_dhahabi=_clean(p.get("dhahabi")),
        grade_category=cat,
        grade_rank=rank,
        sources={k: {"grade": v.get("grade_ar") or v.get("grade_en"), "entry": v.get("entry_id")} for k, v in sources.items()},
        extra={
            "itqan_grade": file_grade,
            "grade_text": grade_ar,
            "grade_inferred": inferred,
            "grade_auto": auto,
            "confidence": p.get("confidence"),
            "teachers": list(p.get("teachers") or []),
            "students": list(p.get("students") or []),
            "origin": prov.get("origin"),
            "merged_ids": [],
        },
    )
    variants = {v for v in (p.get("namings") or []) if v and v != "-"}
    variants.add(full)
    if _clean(p.get("kunya")):
        variants.add(_clean(p["kunya"]).split("،")[0].strip())
    return row, sorted(variants)


def _compatible(a: dict, b: dict) -> bool:
    da, db = a["death_year_h"], b["death_year_h"]
    if da and db and abs(da - db) > 2:
        return False
    ta, tb = normalize(a["tabaqa"] or ""), normalize(b["tabaqa"] or "")
    if ta and tb and ta != tb and not (a["is_companion"] and b["is_companion"]):
        return False
    if a["is_companion"] != b["is_companion"] and da and db:
        return False
    return True


def _weight(r: dict) -> tuple:
    e = r["extra"]
    return (len(e["teachers"]) + len(e["students"]), len(r["sources"]), bool(r["grade_ibn_hajar"]))


def load_profiles() -> None:
    manifest = json.load(open(RIJAL / "manifest.json", encoding="utf-8"))
    rows: dict[str, dict] = {}
    names: dict[str, list[str]] = {}
    for f in manifest["files"]:
        if f["type"] != "profiles":
            continue
        data = json.load(open(RIJAL / f["name"], encoding="utf-8"))
        for pid, p in data.items():
            p["id"] = pid
            row, variants = build_row(p, f["grade"])
            rows[row["external_id"]] = row
            names[row["external_id"]] = variants
        print(f"{f['name']}: {len(data)} notices")
    # ---- fusion des doublons -----------------------------------------------------------------
    groups: dict[str, list[str]] = defaultdict(list)
    for ext, r in rows.items():
        k = person_key(r["name_norm"])
        if k:
            groups[k].append(ext)
    merged_into: dict[str, str] = {}
    for k, members in groups.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda e: _weight(rows[e]), reverse=True)
        mains: list[str] = []
        for e in members:
            target = next((m for m in mains if _compatible(rows[m], rows[e])), None)
            if target is None:
                mains.append(e)
                continue
            main, alias = rows[target], rows[e]
            merged_into[e] = target
            main["extra"]["merged_ids"].append(e)
            names[target] = sorted(set(names[target]) | set(names[e]))
            for key in ("grade_ibn_hajar", "grade_dhahabi", "kunya", "laqab", "nasab", "tabaqa", "city"):
                if not main[key] and alias[key]:
                    if key == "grade_ibn_hajar" and (main["is_companion"] or alias["is_companion"]):
                        continue  # un Compagnon ne reçoit pas une formule de ta'dil venue d'un doublon douteux
                    main[key] = alias[key]
            if not main["death_year_h"] and alias["death_year_h"]:
                main["death_year_h"] = alias["death_year_h"]
            for sk, sv in alias["sources"].items():
                main["sources"].setdefault(sk, sv)
            main["extra"]["teachers"] = sorted(set(main["extra"]["teachers"]) | set(alias["extra"]["teachers"]))
            main["extra"]["students"] = sorted(set(main["extra"]["students"]) | set(alias["extra"]["students"]))
            # jugement : un texte non inféré prime sur un jugement inféré / automatique
            m_ok = not (main["extra"]["grade_inferred"] or main["extra"]["grade_auto"]) and main["extra"]["grade_text"]
            a_ok = not (alias["extra"]["grade_inferred"] or alias["extra"]["grade_auto"]) and alias["extra"]["grade_text"]
            if alias["is_companion"] and not main["is_companion"]:
                main.update(is_companion=True, grade_category="companion", grade_rank=6)
            elif a_ok and not m_ok and not main["is_companion"]:
                main.update(grade_category=alias["grade_category"], grade_rank=alias["grade_rank"])
                main["extra"].update(grade_text=alias["extra"]["grade_text"], grade_inferred=False, grade_auto=False)
    keep = [r for e, r in rows.items() if e not in merged_into]
    print(f"{len(rows)} notices -> {len(keep)} narrateurs après fusion de {len(merged_into)} doublons")
    with engine.begin() as conn:
        conn.execute(delete(NarratorOpinion))
        conn.execute(delete(NarratorName))
        conn.execute(delete(Narrator))
        for i in range(0, len(keep), 2000):
            conn.execute(insert(Narrator), keep[i : i + 2000])
        ids = dict(conn.execute(select(Narrator.external_id, Narrator.id)).all())
        name_rows = []
        for r in keep:
            nid = ids[r["external_id"]]
            seen = set()
            for v in names[r["external_id"]]:
                nn = normalize_name(v)
                if nn and nn not in seen:
                    seen.add(nn)
                    name_rows.append(dict(narrator_id=nid, name_ar=v, name_norm=nn))
        for i in range(0, len(name_rows), 5000):
            conn.execute(insert(NarratorName), name_rows[i : i + 5000])
    print(f"{len(name_rows)} variantes de noms")


_SRC_RE = re.compile(r"\[([^\]]+)\]\s*$")


def load_opinions() -> None:
    """Avis de jarh wa ta'dil (critique -> liste d'avis avec source entre crochets)."""
    ext = json.load(open(EXTERNAL, encoding="utf-8"))
    with session_scope() as s:
        idx: dict[str, list[int]] = {}
        for nn, nid in s.execute(select(NarratorName.name_norm, NarratorName.narrator_id)):
            idx.setdefault(nn, []).append(nid)
        deaths = dict(s.execute(select(Narrator.id, Narrator.death_year_h)).all())
        linked, unlinked, n_op = 0, 0, 0
        for e in ext.values():
            d = e.get("data") or {}
            raw_name = (d.get("الاسم") or "").lstrip(": ").strip()
            base = raw_name.split("(")[0].strip()
            cands = idx.get(normalize_name(base)) or idx.get(normalize_name(e.get("name", ""))) or []
            parts = base.split()
            while len(parts) > 2 and not cands:
                parts = parts[:-1]
                cands = idx.get(normalize_name(" ".join(parts))) or []
            if not cands:
                unlinked += 1
                continue
            dy = _year(d.get("تاريخ الوفاة"))
            nid = cands[0]
            if len(set(cands)) > 1 and dy:
                nid = min(set(cands), key=lambda c: abs((deaths.get(c) or 0) - dy) if deaths.get(c) else 999)
            nar = s.get(Narrator, nid)
            if nar is None:
                unlinked += 1
                continue
            if d.get("الرتبة عند ابن حجر"):
                ih = d["الرتبة عند ابن حجر"]
                cat, rank = classify_grade_text(ih)
                if _COMPANION_TEXT.search(normalize(ih)):
                    nar.grade_ibn_hajar = ih
                    nar.is_companion, nar.grade_category, nar.grade_rank = True, "companion", 6
                elif nar.is_companion:
                    pass  # formule incompatible avec un Compagnon : on l'ignore
                else:
                    nar.grade_ibn_hajar = ih
                    if cat:
                        nar.grade_category, nar.grade_rank = cat, rank
            if d.get("الرتبة عند الذهبي"):
                nar.grade_dhahabi = d["الرتبة عند الذهبي"]
            if d.get("طبقة رواة التقريب") and not nar.tabaqa:
                nar.tabaqa = d["طبقة رواة التقريب"]
            extra = dict(nar.extra or {})
            extra["hadithdb"] = {k: v for k, v in d.items() if k != "الجرح والتعديل" and isinstance(v, str)}
            nar.extra = extra
            for critic, ops in (d.get("الجرح والتعديل") or {}).items():
                for op in ops:
                    m = _SRC_RE.search(op)
                    txt = _SRC_RE.sub("", op).strip()
                    cat, _ = classify_grade_text(txt)
                    kind = "tadil" if cat in ("thiqa", "saduq", "companion") else "jarh" if cat in ("daif", "matruk", "kadhdhab", "maqbul") else "unknown"
                    s.add(NarratorOpinion(narrator_id=nid, critic=critic, opinion=txt, kind=kind, source_book=m.group(1) if m else None))
                    n_op += 1
            linked += 1
        print(f"avis jarh/ta'dil : {n_op} avis, {linked} narrateurs liés, {unlinked} non liés")


if __name__ == "__main__":
    init_db()
    load_profiles()
    load_opinions()
