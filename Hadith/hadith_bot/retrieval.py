"""Pipeline : question -> recherche vectorielle -> chaînes + jugements des narrateurs -> synthèse."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .grading import CATEGORIES, SCALE, grade_chain, score_hadith, score_topic
from .models import Hadith, IsnadLink, Narrator, NarratorOpinion, QueryLog
from . import lexical, vector


def narrator_dict(n: Narrator | None, *, with_opinions: bool = False) -> dict | None:
    if n is None:
        return None
    rank, label_fr, label_ar = CATEGORIES.get(n.grade_category, CATEGORIES["unknown"])
    d = {
        "id": n.id,
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
        v = grade_chain(links)
        out.append({"chain_no": cno, "links": links, "verdict": v.__dict__})
    return out


def hadith_dict(h: Hadith, *, full: bool = True) -> dict:
    d = {
        "id": h.id,
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
        d["reliability"] = score_hadith(h.collection.slug, h.grade_ar, d["chains"])
    return d


def load_hadiths(session: Session, ids: list[int]) -> dict[int, Hadith]:
    rows = session.scalars(
        select(Hadith)
        .where(Hadith.id.in_(ids))
        .options(selectinload(Hadith.collection), selectinload(Hadith.links).selectinload(IsnadLink.narrator))
    ).all()
    return {h.id: h for h in rows}


def hybrid_search(session: Session, queries: list[str], *, k: int, collections: list[str] | None = None) -> list[dict]:
    """Fusion RRF de la recherche vectorielle (toutes formulations) et de la recherche lexicale BM25."""
    where = {"collection": {"$in": collections}} if collections else None
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
        for rank, (hid, _) in enumerate(lexical.search(session, q, k=k * 3)):
            fused[hid] = fused.get(hid, 0.0) + W_LEX / (60 + rank)
            d = info.setdefault(hid, {"hadith_id": hid, "distance": None, "matched_by": []})
            if "lexical" not in d["matched_by"]:
                d["matched_by"].append("lexical")
        for rank, hid in enumerate(lexical.phrase_search(session, q, k=k * 3)):
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


def search_hadiths(session: Session, question: str, *, k: int | None = None, use_llm: bool = True, collections: list[str] | None = None) -> dict[str, Any]:
    k = k or settings.top_k
    queries = [question]
    expansion = None
    if use_llm and settings.llm_enabled:
        from . import llm

        expansion = llm.expand_query(question)
        if expansion:
            queries += [q for q in expansion.get("queries", []) if q and q != question][:5]
    hits = hybrid_search(session, queries, k=k, collections=collections)
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


def ask(session: Session, question: str, *, k: int | None = None, use_llm: bool = True, collections: list[str] | None = None) -> dict[str, Any]:
    payload = search_hadiths(session, question, k=k, use_llm=use_llm, collections=collections)
    answer, llm_used, relevant, synthesis_text = None, False, None, None
    if use_llm and settings.llm_enabled and payload["results"]:
        from . import llm

        out = llm.synthesize(question, payload)
        if out:
            answer, relevant, synthesis_text, llm_used = out["answer"], out["relevant_hadith_ids"], out["synthesis"], True
    # note /5 calculée par le système (jamais par le LLM) sur les hadiths pertinents :
    # choisis par le LLM quand il est actif, sinon par la couverture des termes de la question
    if relevant is None:
        auto = [r["id"] for r in payload["results"] if r.get("relevant_auto")]
        synthesis = score_topic(payload["results"], relevant_ids=auto) if auto else score_topic([], relevant_ids=None)
        if not auto and payload["results"]:
            synthesis.update(score=None, label_fr="Pertinence non établie", label_ar="لم تثبت الصلة",
                             definition="Des hadiths proches ont été trouvés mais aucun ne contient les termes de la question ; sans LLM le système ne note pas.",
                             reasons=["aucun résultat ne contient explicitement les termes de la question (reformulez en arabe ou en anglais, ou activez le LLM qui juge la pertinence)"],
                             hadith_ids=[], considered_ids=[])
    else:
        synthesis = score_topic(payload["results"], relevant_ids=relevant) if relevant else score_topic([], relevant_ids=None)
    synthesis["text"] = synthesis_text or synthesis_plain(payload, synthesis)
    synthesis["by_llm"] = synthesis_text is not None
    synthesis["scale"] = {str(k): {"label_fr": v[0], "label_ar": v[1], "definition": v[2]} for k, v in SCALE.items()}
    payload["synthesis"] = synthesis
    if answer is None:
        answer = format_plain(payload)
    payload["answer"] = answer
    payload["llm_used"] = llm_used
    try:
        session.add(QueryLog(question=question, hadith_ids=[r["id"] for r in payload["results"]], llm_used=llm_used))
        session.commit()
    except Exception:  # journal non bloquant
        session.rollback()
    return payload


def synthesis_plain(payload: dict, syn: dict) -> str:
    """Texte de synthèse déterministe (sans LLM)."""
    if syn["score"] is None:
        return ("Pertinence non établie : les résultats ci-dessous sont proches sémantiquement mais aucun ne contient les termes de la question. "
                "Le système ne note pas l'information dans ce cas ; les notes par hadith restent valables.")
    if syn["score"] == 0 or not payload["results"]:
        return "Aucun hadith pertinent trouvé dans les six recueils indexés pour cette question."
    by_id = {r["id"]: r for r in payload["results"]}
    best = by_id[syn["hadith_ids"][0]]
    refs = ", ".join(by_id[i]["reference"] for i in syn["hadith_ids"][:4])
    n = len(syn["considered_ids"])
    txt = (f"Degré de fiabilité {syn['score']}/5 — {syn['label_fr']} ({syn['label_ar']}). "
           f"{n} hadith(s) retenu(s) parmi les résultats ; attestation la plus solide : {refs}. ")
    if best.get("matn_en"):
        txt += f"Texte principal : « {best['matn_en'][:300].strip()} ». "
    txt += "Note calculée à partir du jugement des recueils et de l'analyse des narrateurs, sans intervention du modèle de langage."
    return txt


def format_synthesis(syn: dict) -> str:
    sc = "?" if syn["score"] is None else syn["score"]
    return "\n".join([f"SYNTHÈSE — {sc}/5 {syn['label_fr']} ({syn['label_ar']})", syn.get("text", ""), *[f"  • {x}" for x in syn["reasons"]]])


def format_plain(payload: dict, *, with_synthesis: bool = False) -> str:
    """Réponse déterministe (sans LLM) : source, chaîne, jugements, verdict (la synthèse est un bloc séparé)."""
    lines = [f"Question : {payload['question']}", ""]
    syn = payload.get("synthesis")
    if syn and with_synthesis:
        lines += [format_synthesis(syn), ""]
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
