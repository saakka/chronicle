"""Jarḥ wa taʿdīl imamite (méthode usūlī) : classification des verdicts sur les narrateurs, verdict de chaîne
(ṣaḥīḥ / muwaththaq / ḥasan / ḍaʿīf) et note /5 fondée sur la gradation de Majlisī (Mirʾāt al-ʿuqūl)."""
from __future__ import annotations

import re

from .arabic import normalize

# catégorie -> (rang, libellé fr, libellé ar)
CATEGORIES_SHIA: dict[str, tuple[int | None, str, str]] = {
    "imam": (6, "Infaillible (معصوم)", "معصوم"),
    "thiqa": (5, "Imamite digne de confiance (ثقة)", "ثقة"),
    "group": (5, "Groupe de maîtres d'al-Kulaynī (عدة من أصحابنا)", "عدة من أصحابنا"),
    "muwaththaq": (4, "Digne de confiance non imamite (موثق)", "موثق"),
    "mamduh": (4, "Imamite loué (ممدوح)", "ممدوح"),
    "majhul": (None, "Inconnu / non qualifié (مجهول، مهمل)", "مجهول"),
    "daif": (2, "Faible (ضعيف)", "ضعيف"),
    "kadhdhab": (0, "Menteur / extrémiste rejeté (كذاب، غال)", "كذاب / غال"),
    "unknown": (None, "Non évalué", "غير مقيم"),
}

_NON_IMAMI = re.compile(r"واقفي|فطحي|ناووسي|زيدي|بتري|عامي|من العامه|غير امامي|كيساني|اسماعيلي")
_RULES = [
    ("kadhdhab", re.compile(r"كذاب|وضاع|يضع|غال\b|غالي|من الغلاه|فاسد المذهب|ملعون|مطعون فيه|متهم بالغلو|لا يلتفت اليه")),
    ("daif", re.compile(r"ضعيف|ضعفه|مضطرب الحديث|متهم|ليس بشيء|لا يعتمد عليه|مخلط|منكر الحديث")),
    ("majhul", re.compile(r"مجهول|مهمل|لم يوثق|لم تثبت وثاقته|لا يعرف|لم يذكر بمدح ولا قدح")),
    ("thiqa", re.compile(r"ثقه|ثبت|عين\b|وجه\b|من اصحاب الاجماع|جليل القدر|عظيم المنزله|صحيح الحديث|لا ينبغي الشك في وثاقته|ثبتت وثاقته|لا شك في وثاقته|من الثقات")),
    ("mamduh", re.compile(r"ممدوح|حسن\b|مدحه|صالح|خير\b|فاضل|له مدح")),
]


def classify_shia(text: str | None) -> tuple[str, int | None]:
    """Verdict d'al-Jawāhirī (résumé de Khūʾī) ou notice classique -> catégorie."""
    if not text:
        return "unknown", None
    raw = re.sub(r"(طريق|طريقه|الطريق|طريقا|طرق|كلا طريقي|طريقي)[^-–]*?(ضعيف|صحيح|مجهول)[^-–]*", " ", text)  # faiblesse d'un chemin, pas du narrateur
    segs = [normalize(x).strip() for x in re.split(r"\s-\s|\s–\s", raw) if x.strip()]
    t = normalize(raw)
    for seg in segs:
        if seg in ("ثقه", "ثقه ثقه", "ثقه عين", "ثقه ثبت", "من اصحاب الاجماع"):
            return ("muwaththaq", 4) if _NON_IMAMI.search(t) else ("thiqa", 5)
        if seg in ("مجهول", "مهمل", "لم يوثق"):
            return "majhul", None
        if seg in ("ضعيف", "ضعيف جدا"):
            return "daif", 2
        if seg in ("ممدوح", "حسن", "له مدح"):
            return "mamduh", 4
    if re.search(r"متحد مع .*الثقه", t):
        return ("muwaththaq", 4) if _NON_IMAMI.search(t) else ("thiqa", 5)
    if re.search(r"متحد مع .*المجهول", t):
        return "majhul", None
    for cat, rx in _RULES:
        if rx.search(t):
            if cat == "thiqa" and _NON_IMAMI.search(t):
                return "muwaththaq", 4
            return cat, CATEGORIES_SHIA[cat][0]
    return "unknown", None


# ------------------------------------------------------------------------------------------
_VERDICTS = {
    "sahih": ("Ṣaḥīḥ : chaîne continue d'imamites dignes de confiance", "صحيح"),
    "muwaththaq": ("Muwaththaq : narrateurs fiables, dont un non-imamite", "موثق"),
    "hasan": ("Ḥasan : imamites fiables ou loués", "حسن"),
    "daif_majhul": ("Ḍaʿīf : un narrateur inconnu ou non identifié", "ضعيف (مجهول)"),
    "daif_mursal": ("Ḍaʿīf : maillon omis ou anonyme (مرسل / مرفوع)", "ضعيف (مرسل)"),
    "daif": ("Ḍaʿīf : un narrateur faible", "ضعيف"),
    "daif_jiddan": ("Très faible : narrateur menteur ou extrémiste rejeté", "ضعيف جدا"),
    "incomplete": ("Chaîne non évaluable", "لم يُقيَّم"),
}
_CONFIDENT = {"exact", "exact+ctx", "relative", "group", "imam"}


def grade_chain_shia(links: list[dict]) -> dict:
    """Verdict usūlī d'une chaîne (maillons sérialisés ; les Imams ne sont pas évalués)."""
    cats: list[tuple[str, str]] = []
    unresolved: list[str] = []
    mursal = False
    for l in links:
        kind = l.get("kind") or "normal"
        if kind == "imam":
            continue
        if kind in ("unnamed", "marfu"):
            mursal = True
            continue
        cands = [l, *l.get("alternatives", [])]
        best = None
        for c in cands:
            n = c.get("narrator")
            if n and n.get("grade_category") not in (None, "unknown"):
                cat = n["grade_category"]
                rank = CATEGORIES_SHIA.get(cat, (None,))[0]
                if best is None or (rank or -1) > (best[1] or -1):
                    best = (cat, rank, c["name"])
        if best is None:
            unresolved.append(l["name"])
        else:
            cats.append((best[0], best[2]))
    notes = ["Verdict indicatif (méthode usūlī, maillon le plus faible) ; le jugement final exige aussi la continuité et l'absence de défaut du texte."]
    weakest = None
    if any(c == "kadhdhab" for c, _ in cats):
        code = "daif_jiddan"
        weakest = next(n for c, n in cats if c == "kadhdhab")
    elif any(c == "daif" for c, _ in cats):
        code = "daif"
        weakest = next(n for c, n in cats if c == "daif")
    elif mursal:
        code = "daif_mursal"
    elif unresolved or any(c == "majhul" for c, _ in cats):
        code = "daif_majhul"
        weakest = unresolved[0] if unresolved else next(n for c, n in cats if c == "majhul")
    elif not cats:
        code = "incomplete"
    elif any(c == "mamduh" for c, _ in cats):
        code = "hasan"
        weakest = next(n for c, n in cats if c == "mamduh")
    elif any(c == "muwaththaq" for c, _ in cats):
        code = "muwaththaq"
        weakest = next(n for c, n in cats if c == "muwaththaq")
    else:
        code = "sahih"
    fr, ar = _VERDICTS[code]
    return {"code": code, "label_fr": fr, "label_ar": ar, "weakest": weakest, "unresolved": unresolved, "anana_count": 0, "notes": notes}


SCALE_SHIA: dict[int, tuple[str, str, str]] = {
    5: ("Établi", "ثابت", "Chaîne ṣaḥīḥ ou jugée ṣaḥīḥ par Majlisī, et corroborée par une autre voie (autre narrateur auprès de l'Imam) ou un autre recueil."),
    4: ("Authentique", "صحيح / موثق", "Jugé ṣaḥīḥ ou muwaththaq par Majlisī (Mirʾāt al-ʿuqūl), chaîne cohérente avec ce jugement."),
    3: ("Bon", "حسن", "Jugé ḥasan, ou chaîne d'imamites loués."),
    2: ("Faible", "ضعيف", "Jugé ḍaʿīf, majhūl, mursal ou marfūʿ par Majlisī, ou chaîne avec un narrateur faible ou inconnu."),
    1: ("Très faible / rejeté", "ضعيف جدا", "Narrateur menteur ou extrémiste rejeté."),
    0: ("Aucune base trouvée", "لا أصل له في المصادر المفهرسة", "Aucun hadith pertinent dans les recueils imamites indexés."),
}
_MAJLISI_LEVEL = [
    (re.compile(r"^(صحيح|موثق|كالصحيح|حسن كالصحيح|موثق كالصحيح|صحيح علي الظاهر)"), 4),
    (re.compile(r"^(حسن|حسن كالموثق|كالموثق|موثق حسن|حسن موثق)"), 3),
    (re.compile(r"^(ضعيف|مجهول|مرسل|مرفوع|موقوف|مقطوع|كالمجهول|منقطع|ضعيف علي المشهور)"), 2),
]
_CHAIN_LEVEL = {"sahih": 4, "muwaththaq": 4, "hasan": 3, "daif": 2, "daif_majhul": 2, "daif_mursal": 2, "daif_jiddan": 1, "incomplete": None}


def classify_majlisi(grade_ar: str | None) -> int | None:
    if not grade_ar:
        return None
    t = normalize(grade_ar)
    for rx, lvl in _MAJLISI_LEVEL:
        if rx.search(t):
            return lvl
    return None


def score_hadith_shia(grade_ar: str | None, chains: list[dict]) -> dict:
    src = classify_majlisi(grade_ar)
    reasons: list[str] = []
    best_code, best_level = None, None
    for c in chains:
        lvl = _CHAIN_LEVEL.get(c["verdict"]["code"])
        if lvl is not None and (best_level is None or lvl > best_level):
            best_code, best_level = c["verdict"]["code"], lvl
    if src is not None:
        reasons.append(f"Majlisī (Mirʾāt al-ʿuqūl) : {grade_ar}")
    if best_code:
        reasons.append(f"narrateurs : {_VERDICTS[best_code][1]}")
    if src is None and best_level is None:
        return {"score": None, "label_fr": "Non évaluable", "label_ar": "غير مقيم", "reasons": reasons}
    score = src if src is not None else best_level
    if src is not None and src >= 3 and best_level is not None and best_level <= 1:
        score -= 1
        reasons.append("divergence : narrateur rejeté identifié dans la chaîne")
    score = max(1, min(4, score))  # le 5 vient de la corroboration (score_topic)
    label_fr, label_ar, _ = SCALE_SHIA[score]
    return {"score": score, "label_fr": label_fr, "label_ar": label_ar, "reasons": reasons}
