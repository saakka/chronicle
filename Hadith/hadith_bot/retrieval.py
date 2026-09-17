"""Pipeline : question -> recherche vectorielle -> chaînes + jugements des narrateurs -> synthèse."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .arabic import strip_tashkil
from .config import settings
from .grading import CATEGORIES, SCALE, grade_chain, scale_for, score_hadith, score_topic
from .grading_shia import CATEGORIES_SHIA, grade_chain_shia, score_hadith_shia
from .models import Hadith, IsnadLink, Narrator, NarratorOpinion, QueryLog
from . import lexical, vector


def narrator_dict(n: Narrator | None, *, with_opinions: bool = False) -> dict | None:
    if n is None:
        return None
    cats = CATEGORIES_SHIA if n.tradition == "shia" else CATEGORIES
    rank, label_fr, label_ar = cats.get(n.grade_category, cats["unknown"])
    d = {
        "id": n.id,
        "tradition": n.tradition,
        "name": n.name_ar,
        "kunya": n.kunya,
        "nasab": n.nasab,
        "tabaqa": n.tabaqa,
        "death_year_h": n.death_year_h,
        "city": n.city,
        "is_companion": n.is_companion,
        "grade_category": n.grade_category,
        "grade_rank": n.grade_rank,
        "grade_label_fr": label_fr,
        "grade_label_ar": label_ar,
        "grade_ibn_hajar": n.grade_ibn_hajar,
        "grade_dhahabi": n.grade_dhahabi,
        "grade_text": (n.extra or {}).get("grade_text"),
        "grade_inferred": bool((n.extra or {}).get("grade_inferred")),
        "grade_auto": bool((n.extra or {}).get("grade_auto")),
        "sources": n.sources or {},
    }
    if with_opinions:
        d["opinions"] = [
            {"critic": o.critic, "opinion": o.opinion, "kind": o.kind, "source": o.source_book} for o in n.opinions
        ]
    return d


def chains_for_hadith(h: Hadith) -> list[dict]:
    """Regroupe les maillons par chaîne/position et calcule le verdict."""
    grouped: dict[int, dict[int, list[IsnadLink]]] = defaultdict(lambda: defaultdict(list))
    for l in h.links:
        grouped[l.chain_no][l.position].append(l)
    out = []
    for cno in sorted(grouped):
        links = []
        for pos in sorted(grouped[cno]):
            alts = grouped[cno][pos]
            main, *others = alts
            links.append(
                {
                    "position": pos,
                    "name": main.name_as_written,
                    "name_norm": main.name_norm,
                    "kind": main.kind or "normal",
                    "term": main.transmission_term,
                    "mode": main.transmission_mode,
                    "is_relative": main.is_relative,
                    "match_method": main.match_method,
                    "match_score": main.match_score,
                    "narrator": narrator_dict(main.narrator),
                    "alternatives": [
                        {"name": o.name_as_written, "match_method": o.match_method, "narrator": narrator_dict(o.narrator)} for o in others
                    ],
                }
            )
        if h.collection.tradition == "shia":
            v = grade_chain_shia(links)
        else:
            v = grade_chain(links).__dict__
        out.append({"chain_no": cno, "links": links, "verdict": v})
    return out


def hadith_dict(h: Hadith, *, full: bool = True) -> dict:
    d = {
        "id": h.id,
        "tradition": h.collection.tradition,
        "collection": h.collection.slug,
        "collection_name": h.collection.name_fr,
        "collection_name_ar": h.collection.name_ar,
        "number": h.hadith_number,
        "reference": f"{h.collection.name_fr} n°{h.hadith_number}",
        "chapter_ar": h.chapter_ar,
        "chapter_en": h.chapter_en,
        "section_ar": h.section_ar,
        "section_en": h.section_en,
        "isnad_ar": h.isnad_ar,
        "matn_ar": h.matn_ar,
        "matn_en": h.matn_en,
        "grade_source_ar": h.grade_ar,
        "grade_source_en": h.grade_en,
    }
    if full:
        d["text_ar"] = h.text_ar
        d["text_en"] = h.text_en
        d["chains"] = chains_for_hadith(h)
        d["meta"] = h.meta or {}
        if h.collection.tradition == "shia":
            d["reliability"] = score_hadith_shia(h.grade_ar, d["chains"])
        else:
            d["reliability"] = score_hadith(h.collection.slug, h.grade_ar, d["chains"])
    return d


def load_hadiths(session: Session, ids: list[int]) -> dict[int, Hadith]:
    rows = session.scalars(
        select(Hadith)
        .where(Hadith.id.in_(ids))
        .options(selectinload(Hadith.collection), selectinload(Hadith.links).selectinload(IsnadLink.narrator))
    ).all()
    return {h.id: h for h in rows}


def hybrid_search(session: Session, queries: list[str], *, k: int, collections: list[str] | None = None, tradition: str | None = None) -> list[dict]:
    """Fusion RRF de la recherche vectorielle (toutes formulations) et de la recherche lexicale BM25."""
    conds = []
    if collections:
        conds.append({"collection": {"$in": collections}})
    if tradition:
        conds.append({"tradition": tradition})
    where = conds[0] if len(conds) == 1 else ({"$and": conds} if conds else None)
    # RRF pondéré : vecteur et BM25 à poids égal, une expression contiguë du matn (« الدين النصيحة »)
    # est un signal fort ; un hadith présent de plusieurs côtés cumule.
    W_VEC, W_LEX, W_PHRASE = 1.0, 1.0, 2.0
    vec = vector.search(queries, k=k * 3, where=where)
    fused: dict[int, float] = {}
    info: dict[int, dict] = {}
    for rank, h in enumerate(vec):
        hid = int(h["hadith_id"])
        fused[hid] = fused.get(hid, 0.0) + W_VEC / (60 + rank)
        info.setdefault(hid, {"hadith_id": hid, "distance": h.get("distance"), "matched_by": []})["matched_by"].append("vector")
    for q in queries:
        for rank, (hid, _) in enumerate(lexical.search(session, q, k=k * 3, tradition=tradition)):
            fused[hid] = fused.get(hid, 0.0) + W_LEX / (60 + rank)
            d = info.setdefault(hid, {"hadith_id": hid, "distance": None, "matched_by": []})
            if "lexical" not in d["matched_by"]:
                d["matched_by"].append("lexical")
        for rank, hid in enumerate(lexical.phrase_search(session, q, k=k * 3, tradition=tradition)):
            fused[hid] = fused.get(hid, 0.0) + W_PHRASE / (60 + rank)
            d = info.setdefault(hid, {"hadith_id": hid, "distance": None, "matched_by": []})
            if "phrase" not in d["matched_by"]:
                d["matched_by"].append("phrase")
    ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
    out = []
    for hid, sc in ranked:
        d = dict(info[hid])
        d["score"] = sc
        out.append(d)
    if collections:  # filtre lexical a posteriori (le filtre vectoriel est déjà appliqué)
        from .models import Collection

        ok = set(session.scalars(select(Hadith.id).join(Collection).where(Collection.slug.in_(collections), Hadith.id.in_([d["hadith_id"] for d in out]))))
        out = [d for d in out if d["hadith_id"] in ok]
    return out[:k]


def search_hadiths(session: Session, question: str, *, k: int | None = None, use_llm: bool = True, collections: list[str] | None = None, tradition: str | None = None) -> dict[str, Any]:
    k = k or settings.top_k
    queries = [question]
    expansion = None
    if use_llm and settings.llm_backend == "anthropic" and settings.llm_enabled:
        from . import llm

        expansion = llm.expand_query(question)
        if expansion:
            queries += [q for q in expansion.get("queries", []) if q and q != question][:5]
    hits = hybrid_search(session, queries, k=k, collections=collections, tradition=tradition)
    ids = [h["hadith_id"] for h in hits]
    hmap = load_hadiths(session, ids)
    # couverture des termes de la question (et de ses reformulations) : pertinence sans LLM
    cov: dict[int, float] = {i: 0.0 for i in ids}
    rare: dict[int, bool] = {i: False for i in ids}
    for q in queries:
        for i, (c, has_rare) in lexical.coverage(session, q, ids).items():
            if c > cov[i]:
                cov[i], rare[i] = c, has_rare
    results = []
    for hit in hits:
        h = hmap.get(hit["hadith_id"])
        if h is None:
            continue
        d = hadith_dict(h)
        d["score"] = round(hit["score"], 4)
        d["distance"] = round(hit.get("distance") or 0.0, 4)
        d["matched_by"] = hit["matched_by"]
        d["term_coverage"] = cov.get(h.id, 0.0)
        # pertinent sans LLM : expression exacte, ou couverture forte incluant le terme le plus rare
        d["relevant_auto"] = "phrase" in hit["matched_by"] or (d["term_coverage"] >= 0.6 and rare.get(h.id, False)) or d["term_coverage"] >= 0.85
        results.append(d)
    return {"question": question, "queries": queries, "expansion": expansion, "results": results}


def _first_sentence(t: str | None, n: int = 140) -> str:
    t = (t or "").strip().replace("\n", " ")
    if not t:
        return ""
    for sep in (". ", "؟", "? ", "! ", "۔"):
        i = t.find(sep, 40)
        if 0 < i < n:
            return t[: i + 1].strip()
    return (t[:n].rsplit(" ", 1)[0] + "…") if len(t) > n else t


def fallback_summary(r: dict) -> dict:
    from .arabic import strip_tashkil

    head_ar = r.get("section_ar") or r.get("chapter_ar") or ""
    head_en = r.get("section_en") or r.get("chapter_en") or ""
    return {
        "ar": _first_sentence(strip_tashkil(head_ar), 90) or _first_sentence(strip_tashkil(r.get("matn_ar") or r.get("text_ar")), 120),
        "en": (head_en.strip() + " — " if head_en else "") + _first_sentence(r.get("matn_en") or r.get("text_en"), 160),
        "by_llm": False,
    }


def attach_summaries(results: list[dict], *, use_llm: bool) -> None:
    """Résumé court ar/en par hadith (repli : titre de section + début du texte)."""
    gen = None
    if use_llm and settings.llm_backend == "anthropic" and settings.llm_enabled and results:
        from . import llm

        gen = llm.summarize(results)
    for r in results:
        g = (gen or {}).get(r["id"])
        r["summary"] = {"ar": g["ar"], "en": g["en"], "by_llm": True} if g and g.get("ar") and g.get("en") else fallback_summary(r)


def _local_available() -> bool:
    if settings.llm_backend != "local" or not settings.llm_enabled:
        return False
    from . import local_llm

    return local_llm.available()


def _scale_dict(tradition: str | None = None) -> dict:
    return {str(k_): {"label_fr": v[0], "label_ar": v[1], "definition": v[2]} for k_, v in scale_for(tradition).items()}


def _score_answer_group(results: list[dict], g: dict, tradition: str | None = None) -> dict:
    by_id = {r["id"]: r for r in results}
    syn = score_topic(results, relevant_ids=g["ids"], tradition=tradition)
    return {
        "answer": g["answer"], "answer_ar": g.get("answer_ar") or "", "answer_en": g.get("answer_en") or "", "ids": g["ids"],
        "unverified_ids": g.get("unverified_ids") or [],
        "score": syn["score"], "label_fr": syn["label_fr"], "label_ar": syn["label_ar"], "reasons": syn["reasons"],
        "sources": [by_id[i]["reference"] for i in g["ids"] if i in by_id],
    }


def ask_local(session: Session, question: str, *, k: int, collections: list[str] | None = None, tradition: str = "sunni") -> dict[str, Any]:
    """Pipeline autonome : le modèle local comprend la question, la recherche hybride trouve les hadiths,
    le modèle juge la pertinence et extrait les réponses, le système note chaque réponse."""
    import time

    from . import local_llm

    t0 = time.time()
    steps: list[dict] = []

    def step(name: str) -> None:
        steps.append({"step": name, "t": round(time.time() - t0, 1)})

    u = local_llm.understand(question, tradition=tradition) or {}
    step("compréhension")
    queries = [question] + u.get("queries_ar", []) + u.get("queries_en", [])
    for extra in (u.get("question_ar"), u.get("question_en")):
        if extra and extra not in queries:
            queries.append(extra)
    hits = hybrid_search(session, queries, k=k, collections=collections, tradition=tradition)
    hmap = load_hadiths(session, [h["hadith_id"] for h in hits])
    results = []
    for hit in hits:
        h = hmap.get(hit["hadith_id"])
        if h is None:
            continue
        d = hadith_dict(h)
        d["score"] = round(hit["score"], 4)
        d["distance"] = round(hit.get("distance") or 0.0, 4)
        d["matched_by"] = hit["matched_by"]
        results.append(d)
    step(f"recherche ({len(results)} candidats)")
    looking_for = u.get("looking_for")
    relevant_ids = local_llm.triage(question, looking_for, results) if results else []
    # garde-fou déterministe : une question sur une personne nommée exige que le hadith la cite
    ents = u.get("entities_ar") or []
    if ents and relevant_ids:
        by_id = {r["id"]: r for r in results}
        relevant_ids = [i for i in relevant_ids if local_llm.mentions_entity(by_id[i].get("text_ar"), ents)]
    step(f"tri ({len(relevant_ids)} pertinents)")
    rel_set = set(relevant_ids)
    lang = u.get("language") or "fr"
    analysis = local_llm.extract(question, looking_for, [r for r in results if r["id"] in rel_set], language=lang) if relevant_ids else {}
    step("extraction des réponses")
    claims = []
    for r in results:
        a = analysis.get(r["id"]) or {}
        r["relevant_auto"] = r["id"] in rel_set
        r["claim"] = strip_tashkil((a.get("answer") or "").strip())
        r["summary"] = {"ar": a.get("summary_ar") or "", "en": a.get("summary_en") or "", "by_llm": True} if (a.get("summary_ar") or a.get("summary_en")) else fallback_summary(r)
        if r["id"] in rel_set and a.get("answer"):
            c = local_llm.verify_claim({"id": r["id"], "answer": strip_tashkil(a["answer"]).strip(), "answer_key": a.get("answer_key") or ""}, r.get("matn_ar") or r.get("text_ar"))
            r["claim_verified"] = c["verified"]
            claims.append(c)
    groups = local_llm.group(question, claims) if claims else []
    # réponses dans la langue de la question (le modèle recopie souvent l'arabe du hadith) ; l'original reste visible
    if groups:
        import re as _re

        arabic = _re.compile(r"[\u0600-\u06FF]")
        latin = _re.compile(r"[A-Za-z]")
        need = [g for g in groups if (lang in ("fr", "en") and arabic.search(g["answer"])) or (lang == "ar" and latin.search(g["answer"]) and not arabic.search(g["answer"]))]
        if need:
            translated = local_llm.translate_answers([g["answer"] for g in need], lang)
            for g, tr in zip(need, translated):
                if tr != g["answer"]:
                    if arabic.search(g["answer"]):
                        g["answer_ar"] = g["answer"]
                    g["answer"] = tr
    step(f"regroupement ({len(groups)} réponse(s))")
    answers = [_score_answer_group(results, g, tradition) for g in groups]
    rel = set(relevant_ids)
    results.sort(key=lambda r: (0 if r["id"] in rel else 1, -r["score"]))
    synthesis = score_topic(results, relevant_ids=relevant_ids, tradition=tradition) if relevant_ids else score_topic([], relevant_ids=None, tradition=tradition)
    scored = [a["score"] for a in answers if a["score"] is not None]
    if scored:
        synthesis["score"] = max(scored)
        synthesis["label_fr"], synthesis["label_ar"], synthesis["definition"] = scale_for(tradition)[synthesis["score"]]
    synthesis["text"] = answers_text(answers, u.get("language") or "fr") if answers else synthesis_plain({"question": question, "results": results}, synthesis)
    synthesis["by_llm"] = False
    synthesis["tradition"] = tradition
    # réponse courte en tête : rédigée par le modèle à partir des seules réponses extraites, vérifiée par les nombres
    best = max(answers, key=lambda a: ((a["score"] or 0), len(a["ids"]))) if answers else None
    short = None
    if answers:
        short = local_llm.short_answer(question, answers, language=lang)
        if short and any(short.strip() == a["answer"].strip() for a in answers):
            short = None  # copie verbatim d'une réponse : pas de valeur ajoutée
        short = short or best["answer"]
    synthesis["short"] = short
    keys = [local_llm.key_values(a["answer"]) for a in answers]
    synthesis["key"] = " · ".join(k for k in dict.fromkeys(keys) if k) if answers else ""
    synthesis["scale"] = _scale_dict(tradition)
    step("synthèse")
    payload = {"question": question, "tradition": tradition, "queries": queries, "understanding": u, "results": results, "answers": answers, "synthesis": synthesis, "steps": steps}
    payload["answer"] = format_plain(payload)
    payload["llm_used"] = True
    payload["llm_backend"] = "local"
    return payload


TRADITION_LABELS = {"sunni": ("Sunna", "أهل السنة"), "shia": ("Chia (imamite)", "الإمامية")}


def compare(sunni: dict, shia: dict) -> dict:
    """Indicateur factuel de convergence entre les deux traditions : valeurs clés communes ou non. Aucun arbitrage."""
    from .local_llm import key_values

    def keys(p: dict) -> list[str]:
        return [k for k in (key_values(a["answer"]) for a in p.get("answers", [])) if k]

    ks, kh = keys(sunni), keys(shia)
    if not ks or not kh:
        status, label = "indetermine", "Comparaison impossible : réponses chiffrées absentes d'un côté"
    elif set(ks) & set(kh):
        status, label = "concordant", "Concordant : au moins une valeur commune"
    else:
        status, label = "divergent", "Divergent : aucune valeur commune"
    return {"status": status, "label_fr": label, "sunni_values": ks, "shia_values": kh,
            "note": "Chaque tradition est notée par sa propre science du rijal ; l'outil décrit, il ne tranche pas."}


def ask_both(session: Session, question: str, *, k: int | None = None, use_llm: bool = True) -> dict[str, Any]:
    out = {"mode": "both", "question": question}
    for trad in ("sunni", "shia"):
        out[trad] = ask(session, question, k=k, use_llm=use_llm, tradition=trad)
    out["comparison"] = compare(out["sunni"], out["shia"])
    return out


_T = {
    "fr": ("{a} réponse(s) distincte(s) trouvée(s) dans {n} hadith(s) ; la mieux attestée : {best} ({s}/5).", "aucune réponse explicite trouvée dans les six recueils"),
    "en": ("{a} distinct answer(s) found in {n} hadith(s); best attested: {best} ({s}/5).", "no explicit answer found in the six collections"),
    "ar": ("عُثر على {a} جواب مختلف في {n} حديثا؛ أقواها إسنادا: {best} ({s}/5).", "لم يُعثر على جواب صريح في الكتب الستة"),
}


def answers_text(answers: list[dict], lang: str) -> str:
    """Synthèse déterministe (aucun texte libre du modèle) dans la langue de la question."""
    fmt, none = _T.get(lang, _T["fr"])
    if not answers:
        return none
    best = max(answers, key=lambda a: ((a["score"] or 0), len(a["ids"])))
    n = sum(len(a["ids"]) for a in answers)
    return fmt.format(a=len(answers), n=n, best=best["answer"].rstrip("."), s="?" if best["score"] is None else best["score"])


def ask(session: Session, question: str, *, k: int | None = None, use_llm: bool = True, collections: list[str] | None = None, tradition: str = "sunni") -> dict[str, Any]:
    k = k or settings.top_k
    if tradition == "both":
        return ask_both(session, question, k=k, use_llm=use_llm)
    if use_llm and _local_available():
        payload = ask_local(session, question, k=k, collections=collections, tradition=tradition)
        _log_query(session, question, payload)
        return payload
    use_anthropic = use_llm and settings.llm_backend == "anthropic" and settings.llm_enabled
    payload = search_hadiths(session, question, k=k, use_llm=use_anthropic, collections=collections, tradition=tradition)
    payload["tradition"] = tradition
    answer, llm_used, relevant, synthesis_text = None, False, None, None
    attach_summaries(payload["results"], use_llm=use_anthropic)
    if use_anthropic and payload["results"]:
        from . import llm

        out = llm.synthesize(question, payload)
        if out:
            answer, relevant, synthesis_text, llm_used = out["answer"], out["relevant_hadith_ids"], out["synthesis"], True
    # note /5 calculée par le système (jamais par le LLM) sur les hadiths pertinents :
    # choisis par le LLM quand il est actif, sinon par la couverture des termes de la question
    if relevant is None:
        auto = [r["id"] for r in payload["results"] if r.get("relevant_auto")]
        synthesis = score_topic(payload["results"], relevant_ids=auto, tradition=tradition) if auto else score_topic([], relevant_ids=None, tradition=tradition)
        if not auto and payload["results"]:
            synthesis.update(score=None, label_fr="Pertinence non établie", label_ar="لم تثبت الصلة",
                             definition="Des hadiths proches ont été trouvés mais aucun ne contient les termes de la question ; sans modèle de langage le système ne note pas.",
                             reasons=["aucun résultat ne contient explicitement les termes de la question (reformulez en arabe ou en anglais, ou activez l'analyse par le modèle)"],
                             hadith_ids=[], considered_ids=[])
    else:
        synthesis = score_topic(payload["results"], relevant_ids=relevant, tradition=tradition) if relevant else score_topic([], relevant_ids=None, tradition=tradition)
    synthesis["text"] = synthesis_text or synthesis_plain(payload, synthesis)
    synthesis["by_llm"] = synthesis_text is not None
    synthesis["tradition"] = tradition
    synthesis["scale"] = _scale_dict(tradition)
    payload["synthesis"] = synthesis
    payload["answers"] = []
    payload["answer"] = answer or format_plain(payload)
    payload["llm_used"] = llm_used
    payload["llm_backend"] = "anthropic" if llm_used else "none"
    _log_query(session, question, payload)
    return payload


def _log_query(session: Session, question: str, payload: dict) -> None:
    try:
        session.add(QueryLog(question=question, hadith_ids=[r["id"] for r in payload["results"]], llm_used=bool(payload.get("llm_used"))))
        session.commit()
    except Exception:  # journal non bloquant
        session.rollback()


def synthesis_plain(payload: dict, syn: dict) -> str:
    """Texte de synthèse déterministe (sans LLM)."""
    if syn["score"] is None:
        return ("Pertinence non établie : les résultats ci-dessous sont proches sémantiquement mais aucun ne contient les termes de la question. "
                "Le système ne note pas l'information dans ce cas ; les notes par hadith restent valables.")
    if syn["score"] == 0 or not payload["results"]:
        return "Aucun hadith pertinent trouvé dans les six recueils indexés pour cette question."
    by_id = {r["id"]: r for r in payload["results"]}
    refs = ", ".join(by_id[i]["reference"] for i in syn["hadith_ids"][:3])
    n = len(syn["considered_ids"])
    return f"{n} hadith(s) retenu(s) ; attestation la plus solide : {refs}."


def format_synthesis(syn: dict) -> str:
    sc = "?" if syn["score"] is None else syn["score"]
    head = [f"RÉPONSE : {syn['short']}", ""] if syn.get("short") else []
    return "\n".join([*head, f"SYNTHÈSE — {sc}/5 {syn['label_fr']} ({syn['label_ar']})", syn.get("text", ""), *[f"  • {x}" for x in syn["reasons"]]])


def format_plain(payload: dict, *, with_synthesis: bool = False) -> str:
    """Réponse déterministe (sans LLM) : source, chaîne, jugements, verdict (la synthèse est un bloc séparé)."""
    lines = [f"Question : {payload['question']}", ""]
    syn = payload.get("synthesis")
    if syn and with_synthesis:
        lines += [format_synthesis(syn), ""]
    if payload.get("answers"):
        lines.append("RÉPONSES TROUVÉES")
        for a in payload["answers"]:
            sc = "?" if a["score"] is None else a["score"]
            lines.append(f"  [{sc}/5 {a['label_ar']}] {a['answer']} — sources : {', '.join(a['sources'][:5])}")
        lines.append("")
    if not payload["results"]:
        return "\n".join(lines + ["Aucun hadith pertinent trouvé dans les six recueils indexés."])
    for i, r in enumerate(payload["results"], 1):
        rel = r.get("reliability") or {}
        note = f" — fiabilité {rel['score']}/5 ({rel['label_ar']})" if rel.get("score") is not None else ""
        lines.append(f"{i}. {r['reference']} — {r['collection_name_ar']} — jugement du recueil : {r['grade_source_ar'] or '—'}{note}")
        if r.get("matn_ar"):
            lines.append("   " + r["matn_ar"][:400].replace("\n", " "))
        for c in r["chains"]:
            parts = []
            for l in c["links"]:
                n = l["narrator"]
                g = n["grade_label_ar"] if n else "؟"
                parts.append(f"{l['name']} [{g}]")
            lines.append(f"   Isnad {c['chain_no'] + 1} : " + " ← ".join(parts))
            lines.append(f"   Verdict indicatif : {c['verdict']['label_fr']}")
        lines.append("")
    return "\n".join(lines)


_REPORT_CACHE: dict[int, str | None] = {}


def hadith_report(session: Session, hadith_id: int, *, use_llm: bool = True) -> dict | None:
    """Données complètes pour le rapport d'un hadith : fiche, notices et avis des narrateurs, narration LLM (optionnelle)."""
    h = load_hadiths(session, [hadith_id]).get(hadith_id)
    if h is None:
        return None
    d = hadith_dict(h)
    attach_summaries([d], use_llm=use_llm)
    ids = {l["narrator"]["id"] for c in d["chains"] for l in c["links"] for a in [l, *l["alternatives"]] if a.get("narrator") for l in [a]}
    narrators: dict[int, dict] = {}
    if ids:
        rows = session.scalars(select(Narrator).where(Narrator.id.in_(ids)).options(selectinload(Narrator.opinions))).all()
        for n in rows:
            nd = narrator_dict(n, with_opinions=True)
            nd["hadith_count"] = session.scalar(select(func.count(func.distinct(IsnadLink.hadith_id))).where(IsnadLink.narrator_id == n.id))
            narrators[n.id] = nd
    report = {"hadith": d, "narrators": {str(k): v for k, v in narrators.items()}, "narrative": None, "scale": {str(k): {"label_fr": v[0], "label_ar": v[1], "definition": v[2]} for k, v in SCALE.items()}}
    if use_llm and settings.llm_backend == "anthropic" and settings.llm_enabled:
        if hadith_id not in _REPORT_CACHE:
            from . import llm

            _REPORT_CACHE[hadith_id] = llm.report_narrative(report)
        report["narrative"] = _REPORT_CACHE[hadith_id]
    return report
