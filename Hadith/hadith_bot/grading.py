"""Classification des formules de Jarh wa Ta'dil et évaluation globale d'une chaîne."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .arabic import normalize

# catégorie -> (rang, libellé fr, libellé ar)
CATEGORIES: dict[str, tuple[int | None, str, str]] = {
    "companion": (6, "Compagnon (صحابي)", "صحابي"),
    "thiqa": (5, "Digne de confiance (ثقة)", "ثقة"),
    "saduq": (4, "Véridique (صدوق)", "صدوق"),
    "maqbul": (3, "Acceptable si corroboré (مقبول / لين)", "مقبول"),
    "daif": (2, "Faible (ضعيف)", "ضعيف"),
    "matruk": (1, "Abandonné (متروك)", "متروك"),
    "kadhdhab": (0, "Menteur / faussaire (كذاب / وضاع)", "كذاب"),
    "unknown": (None, "Non évalué / inconnu (مجهول)", "مجهول"),
}

# Marâtib al-jarh wa-l-ta'dil (formules d'Ibn Hajar / Ibn Abi Hatim), testées dans l'ordre : du plus grave au plus fort.
_RULES: list[tuple[str, re.Pattern]] = [
    ("kadhdhab", re.compile(r"كذاب|وضاع|يضع الحديث|دجال|متهم بالكذب|متهم بالوضع|يكذب|يضع")),
    ("matruk", re.compile(r"متروك|ذاهب الحديث|ساقط|هالك|تالف|لا يكتب حديثه|ليس بثقه|ليس بشيء|منكر الحديث|واه بمره|لا يحل الاحتجاج|لا تحل الروايه")),
    # martaba 6-7 d'Ibn Hajar : véridique mais à corroborer
    ("maqbul", re.compile(r"صدوق (يخطي|يهم|له اوهام|سيء الحفظ|سيىء الحفظ|كثير الخطا|كثير الغلط|تغير|ربما وهم|يغرب|له مناكير|ضعيف الحفظ)|مقبول|مستور|مجهول الحال|لين الحديث|فيه لين|^لين$|صالح الحديث|يكتب حديثه|شيخ$|صدوق يدلس|صدوق رمي|صدوق في|صدوق يخطئ")),
    ("daif", re.compile(r"ضعيف|ضعفوه|واه|منكر|مضطرب|ليس بالقوي|ليس بقوي|لا يحتج به|فيه ضعف|ضعفه|سيء الحفظ|سيىء الحفظ|كثير الخطا|كثير الغلط|كثير الاوهام|اختلط|مجهول|لا يعرف|يخطي كثيرا|كثير الوهم|فيه نظر|سكتوا عنه")),
    ("companion", re.compile(r"صحابي|صحابيه|له صحبه|لها صحبه|من الصحابه|صحبه")),
    ("thiqa", re.compile(r"ثقه|ثبت|حجه|امام|حافظ|متقن|عدل|ضابط|اثبت|من الاثبات|اوثق|صدوق ثبت|وثقه|ثقات|احد الاعلام")),
    ("saduq", re.compile(r"صدوق|محله الصدق|صالح|لا باس|ليس به باس|ما اعلم به باسا|شيخ وسط|جيد الحديث|حسن الحديث|مستقيم الحديث|يحتج به|محتج به|وسط")),
]


def classify_grade_text(text: str | None) -> tuple[str | None, int | None]:
    """Attribue une catégorie à une formule (ex. « ثقة ثبت » -> thiqa, « صدوق يخطئ » -> maqbul)."""
    if not text:
        return None, None
    t = normalize(text)
    if t.startswith("استنباط"):
        return None, None
    # les formules composées : « ثقة لكنه اختلط » -> on garde la nuance la plus prudente si elle est explicite
    if re.fullmatch(r"(ذكره|ذكرها) ابن حبان في الثقات|وثقه ابن حبان", t):
        return "saduq", 4  # tawthiq d'Ibn Hibban seul : réputé indulgent (تساهل), traité comme صدوق
    for cat, rx in _RULES:
        if rx.search(t):
            return cat, CATEGORIES[cat][0]
    return None, None


@dataclass
class ChainVerdict:
    code: str  # sahih_rijal | hasan_rijal | daif | daif_jiddan | incomplete
    label_fr: str
    label_ar: str
    weakest: str | None  # nom du maillon le plus faible
    unresolved: list[str]
    anana_count: int
    notes: list[str]


def _best_rank(link: dict) -> tuple[int | None, str, bool]:
    """Pour un niveau avec co-rapporteurs, on retient le mieux noté (l'un des deux suffit)."""
    best, name, resolved = None, link["name"], False
    for cand in [link, *link.get("alternatives", [])]:
        nar = cand.get("narrator")
        if nar:
            resolved = True
            r = nar.get("grade_rank")
            if r is not None and (best is None or r > best):
                best, name = r, cand["name"]
    return best, name, resolved


def grade_chain(links: list[dict]) -> ChainVerdict:
    """`links` : maillons sérialisés (name, mode, is_relative, narrator{grade_rank,...}, alternatives[])."""
    unresolved: list[str] = []
    ranks: list[tuple[int, str]] = []
    anana = 0
    notes: list[str] = []
    for l in links:
        if l.get("mode") in ("anana", "an"):
            anana += 1
        best, name, resolved = _best_rank(l)
        if not resolved:
            unresolved.append(l["name"])
        elif best is None:
            unresolved.append(f"{name} (sans jugement)")
        else:
            ranks.append((best, name))
    if any(l.get("inferred") for l in links):
        notes.append("Jonction après تحويل (ح) inférée : la fin de chaîne est partagée avec la chaîne suivante.")
    inferred = [
        (c.get("narrator") or {}).get("name") for l in links for c in [l, *l.get("alternatives", [])]
        if c.get("narrator") and (c["narrator"].get("grade_inferred") or c["narrator"].get("grade_auto"))
    ]
    if inferred:
        notes.append("Jugement non textuel (inféré des isnads ou automatique) pour : " + "، ".join(n for n in inferred if n) + ".")
    if anana:
        notes.append(f"{anana} maillon(s) en عنعنة (عن / أن) : la continuité suppose l'absence de tadlis.")
    if not ranks and unresolved:
        return ChainVerdict("incomplete", "Chaîne non évaluable (narrateurs non identifiés)", "لم يُقيَّم", None, unresolved, anana, notes)
    min_rank, weakest = min(ranks, key=lambda t: t[0]) if ranks else (None, None)
    if min_rank is not None and min_rank <= 1:
        code, fr, ar = "daif_jiddan", "Très faible : contient un narrateur abandonné ou accusé de mensonge", "ضعيف جدا"
    elif min_rank == 2:
        code, fr, ar = "daif", "Faible (ضعيف) : contient un narrateur faible", "ضعيف"
    elif min_rank == 3:
        code, fr, ar = "hasan_in_tubia", "Hasan sous réserve de corroboration : un narrateur « صدوق يهم / مقبول » (حسن إن توبع وإلا فلين)", "حسن إن توبع"
    elif unresolved:
        code, fr, ar = "incomplete", f"Évaluation partielle : {len(unresolved)} maillon(s) non identifié(s), les autres sont fiables", "غير مكتمل"
    elif min_rank == 4:
        code, fr, ar = "hasan_rijal", "Hasan par ses narrateurs (رجاله صدوقون)", "حسن (رجاله)"
    else:
        code, fr, ar = "sahih_rijal", "Sahih par ses narrateurs (رجاله ثقات)", "صحيح (رجاله)"
    notes.append("Évaluation indicative fondée sur les narrateurs (maillon le plus faible). Le jugement final exige aussi la continuité (اتصال), l'absence de شذوذ et de علة.")
    return ChainVerdict(code, fr, ar, weakest, unresolved, anana, notes)


# ---------------------------------------------------------------------------------------------
# Échelle de fiabilité sur 5 (synthèse) : jugement du recueil / d'al-Albânî croisé avec l'analyse des narrateurs
# ---------------------------------------------------------------------------------------------
SCALE: dict[int, tuple[str, str, str]] = {
    5: ("Établi", "ثابت", "Rapporté dans Sahih al-Bukhari ou Sahih Muslim avec une chaîne entièrement identifiée de narrateurs ثقة, ou attesté par plusieurs rapports authentiques indépendants."),
    4: ("Authentique", "صحيح", "Jugé صحيح par le recueil ou par al-Albânî, chaîne cohérente avec ce jugement."),
    3: ("Bon / acceptable", "حسن", "Jugé حسن, ou chaîne dont un narrateur est صدوق يهم / مقبول, ou chaîne partiellement identifiée."),
    2: ("Faible", "ضعيف", "Jugé ضعيف par le recueil, ou chaîne contenant un narrateur faible."),
    1: ("Très faible / rejeté", "ضعيف جدا", "Narrateur abandonné ou accusé de mensonge, ou jugement منكر / شاذ / موضوع."),
    0: ("Aucune base trouvée", "لا أصل له في المصادر المفهرسة", "Aucun hadith pertinent dans les six recueils indexés (cela ne prouve pas l'inexistence ailleurs)."),
}

_VERDICT_LEVEL = {"sahih_rijal": 4, "hasan_rijal": 3, "hasan_in_tubia": 3, "daif": 2, "daif_jiddan": 1, "incomplete": None}
_CONFIDENT = {"exact", "exact+ctx", "relative"}


def classify_source_grade(grade_ar: str | None) -> tuple[int | None, list[str]]:
    """Jugement du recueil (LK / al-Albânî) -> niveau 1..4 + remarques (موقوف / مقطوع)."""
    if not grade_ar:
        return None, []
    t = normalize(grade_ar)
    notes = []
    if "موقوف" in t:
        notes.append("rapport موقوف : parole ou acte d'un Compagnon, non attribué au Prophète ﷺ")
    if "مقطوع" in t:
        notes.append("rapport مقطوع : parole d'un Successeur, non attribuée au Prophète ﷺ")
    if re.search(r"موضوع|باطل|منكر|شاذ|ضعيف جدا|متروك|كذب|لا اصل", t):
        return 1, notes
    if "ضعيف" in t:
        return 2, notes
    if "صحيح" in t:
        return 4, notes
    if "حسن" in t:
        return 3, notes
    return None, notes


def _weakest_link(chain: dict) -> dict | None:
    name = chain["verdict"].get("weakest")
    for l in chain["links"]:
        if l["name"] == name:
            return l
    return None


def score_hadith(collection_slug: str, grade_ar: str | None, chains: list[dict]) -> dict:
    """Note /5 d'un hadith : base = jugement du recueil ; l'analyse des narrateurs relève (Sahihayn +
    رجاله ثقات -> 5) ou abaisse (narrateur faible identifié avec certitude) d'un cran."""
    src, notes = classify_source_grade(grade_ar)
    reasons: list[str] = []
    best_chain, best_level = None, None
    for c in chains:
        lvl = _VERDICT_LEVEL.get(c["verdict"]["code"])
        if lvl is not None and (best_level is None or lvl > best_level):
            best_chain, best_level = c, lvl
    if src is not None:
        reasons.append(f"jugement du recueil : {grade_ar}")
    if best_chain is not None:
        reasons.append(f"narrateurs : {best_chain['verdict']['label_ar']}")
    elif chains:
        reasons.append("chaîne non entièrement identifiée")
    if src is None and best_level is None:
        return {"score": None, "label_fr": "Non évaluable", "label_ar": "غير مقيم", "reasons": reasons + notes}
    score = src if src is not None else best_level
    if collection_slug in ("bukhari", "muslim") and best_level == 4:
        score = 5
        reasons.append("Sahihayn + chaîne intégralement ثقة")
    elif src is not None and src >= 3 and best_level is not None and best_level <= 2 and best_chain is not None:
        weak = _weakest_link(best_chain)
        if weak and weak.get("match_method") in _CONFIDENT:
            score -= 1
            reasons.append(f"divergence : {weak['name']} jugé faible dans la base des narrateurs")
        else:
            reasons.append("divergence non retenue : narrateur faible apparié de façon ambiguë")
    score = max(1, min(5, score))
    label_fr, label_ar, _ = SCALE[score]
    return {"score": score, "label_fr": label_fr, "label_ar": label_ar, "reasons": reasons + notes}


def _companion_of(result: dict) -> str | None:
    """Dernier maillon humain : le Compagnon (sunnite) ou le narrateur auprès de l'Imam (imamite)."""
    for c in result.get("chains", []):
        for l in reversed(c["links"]):
            if (l.get("kind") or "normal") != "imam":
                return l.get("name_norm") or l["name"]
    return None


def scale_for(tradition: str | None) -> dict[int, tuple[str, str, str]]:
    if tradition == "shia":
        from .grading_shia import SCALE_SHIA

        return SCALE_SHIA
    return SCALE


def score_topic(results: list[dict], relevant_ids: list[int] | None = None, tradition: str | None = None) -> dict:
    """Synthèse : note /5 de l'information à partir des hadiths pertinents (choisis par le LLM, sinon
    par le score de recherche)."""
    SCALE = scale_for(tradition)  # noqa: N806 - libellés propres à la tradition
    if not results:
        s = SCALE[0]
        return {"score": 0, "label_fr": s[0], "label_ar": s[1], "definition": s[2], "reasons": [s[2]], "hadith_ids": [], "considered_ids": []}
    if relevant_ids:
        considered = [r for r in results if r["id"] in set(relevant_ids)] or results[:3]
    else:
        best = results[0]["score"]
        considered = [r for r in results if r["score"] >= 0.5 * best][:5] or results[:3]
        if len(considered) < 3:
            considered = results[:3]
    scored = [r for r in considered if r.get("reliability", {}).get("score") is not None]
    if not scored:
        s = SCALE[0]
        return {"score": 0, "label_fr": s[0], "label_ar": s[1], "definition": s[2], "reasons": ["hadiths trouvés mais sans jugement exploitable"], "hadith_ids": [], "considered_ids": [r["id"] for r in considered]}
    top = max(r["reliability"]["score"] for r in scored)
    strong = [r for r in scored if r["reliability"]["score"] >= 4]
    reasons: list[str] = []
    best = next(r for r in scored if r["reliability"]["score"] == top)
    reasons.append(f"meilleure attestation : {best['reference']} ({', '.join(best['reliability']['reasons'][:2])})")
    if top == 4 and len(strong) >= 2:
        colls = {r["collection"] for r in strong}
        comps = {_companion_of(r) for r in strong} - {None}
        if len(colls) >= 2 or len(comps) >= 2:
            top = 5
            reasons.append(f"corroboré par {len(strong) - 1} autre(s) rapport(s) authentique(s) ({', '.join(sorted(colls))})")
    elif len(strong) >= 2:
        reasons.append(f"{len(strong)} rapports authentiques retenus")
    weak = [r for r in scored if r["reliability"]["score"] <= 2]
    if weak and top >= 4:
        reasons.append(f"{len(weak)} rapport(s) faible(s) également trouvé(s), sans incidence sur les rapports authentiques")
    label_fr, label_ar, definition = SCALE[top]
    return {
        "score": top,
        "label_fr": label_fr,
        "label_ar": label_ar,
        "definition": definition,
        "reasons": reasons,
        "hadith_ids": [r["id"] for r in scored if r["reliability"]["score"] == top] or [best["id"]],
        "considered_ids": [r["id"] for r in considered],
    }
