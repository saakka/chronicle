"""Couche LLM (Claude) : traduction/expansion de la requête et mise en forme de la réponse.

Le modèle ne juge jamais lui-même : il reçoit les hadiths trouvés, les chaînes extraites et les
jugements issus de la base SQL, et se limite à les présenter. Toute absence de données doit être
dite explicitement. Sans clé API, la couche est simplement ignorée (réponse déterministe).
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

import anthropic
from pydantic import BaseModel, Field

from .config import settings

log = logging.getLogger(__name__)

SYSTEM_EXPAND = (
    "Tu es un moteur de reformulation pour la recherche de hadiths dans les six recueils canoniques. "
    "À partir d'une question (français, anglais ou arabe), produis 4 à 6 requêtes courtes de recherche : "
    "au moins 2 en arabe (vocabulaire des hadiths, sans tashkil, ex. « إنما الأعمال بالنيات », « صيام يوم عاشوراء ») "
    "et 2 en anglais (termes des traductions classiques : « fasting on the day of Ashura »). "
    "Ne réponds pas à la question, n'invente aucun hadith : uniquement des formulations de recherche."
)

SYSTEM_SYNTH = """Tu es un assistant spécialisé en sciences du hadith (علوم الحديث) et en critique des narrateurs (الجرح والتعديل).
Tu reçois un JSON contenant : la question de l'utilisateur, les hadiths trouvés par recherche sémantique dans les six recueils
(Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah), pour chacun sa chaîne d'isnad extraite automatiquement
et, pour chaque narrateur, le jugement issu de la base relationnelle (Taqrib al-Tahdhib d'Ibn Hajar, al-Dhahabi, avis de jarh/ta'dil).

RÈGLES STRICTES :
1. Ne cite QUE les hadiths présents dans le JSON. N'ajoute jamais un hadith, un narrateur, un jugement ou une référence de mémoire.
2. Les jugements sur les narrateurs viennent uniquement des champs fournis (grade_label, grade_ibn_hajar, grade_dhahabi, opinions). Si un narrateur n'est pas identifié (narrator = null) ou sans jugement, écris-le clairement (« non identifié dans la base »).
3. Le verdict de chaîne fourni (verdict.label_fr) est indicatif, fondé sur le maillon le plus faible ; rappelle que le jugement final exige aussi la continuité, l'absence de شذوذ et de علة, et cite le jugement du recueil / d'al-Albani (grade_source_ar) quand il existe.
4. Réponds dans la langue de la question (français par défaut). Les textes arabes (matn, noms) restent en arabe, avec traduction/translittération.
5. Tu renvoies un objet structuré :
   - relevant_hadith_ids : les ids des hadiths du JSON qui répondent réellement à la question (vide si aucun n'est pertinent) ;
   - synthesis : 3 à 6 phrases qui répondent directement à la question à partir de ces seuls hadiths, en citant les références (ex. « Sahih al-Bukhari n°2004 »). Pas de note chiffrée : la note /5 est calculée par le système à partir des jugements.
   - answer : la réponse détaillée : pour chaque hadith pertinent, référence exacte, extrait du matn en arabe + traduction, chaîne « A ← B ← C » avec le jugement de chaque maillon, verdict indicatif + jugement du recueil ; puis les limites (narrateurs non identifiés, chaînes partielles, hadiths hors sujet écartés).
6. Aucune fatwa : tu présentes les sources et leur fiabilité, tu ne tranches pas les questions juridiques."""


class SynthesisOutput(BaseModel):
    relevant_hadith_ids: list[int] = Field(description="ids (champ id du JSON) des hadiths qui répondent à la question")
    synthesis: str = Field(description="réponse courte à la question fondée sur ces hadiths, avec références, sans note chiffrée")
    answer: str = Field(description="réponse détaillée : sources, chaînes, jugements, limites")


class HadithSummary(BaseModel):
    id: int
    ar: str = Field(description="une phrase en arabe (≤ 25 mots) : ce que dit / raconte ce hadith")
    en: str = Field(description="one English sentence (≤ 25 words): what this hadith says / its story")


class SummaryBatch(BaseModel):
    items: list[HadithSummary]


SYSTEM_SUMMARY = (
    "Pour chaque hadith fourni (id, texte arabe, traduction), écris une phrase en arabe et une phrase en anglais, "
    "≤ 25 mots chacune, qui disent de quoi parle le hadith (son propos ou son histoire), sans jugement d'authenticité, "
    "sans commentaire, sans ajouter d'information absente du texte. Rends exactement un item par id."
)

SYSTEM_REPORT = """Tu rédiges, en français, un rapport d'analyse d'un hadith à partir d'un JSON fermé (texte, chaîne extraite,
notices et avis de critiques sur chaque narrateur, verdict indicatif, jugement du recueil). Règles : n'ajoute aucune donnée
absente du JSON ; si un narrateur n'est pas identifié, dis-le ; pas de fatwa. Structure en 4 courts paragraphes :
1) Le propos du hadith (2-3 phrases, avec les mots arabes clés) ; 2) La chaîne : qui rapporte de qui, avec le jugement de chaque
maillon et les points d'attention (عنعنة, narrateur مقبول, ambiguïtés d'identification) ; 3) L'évaluation : jugement du recueil /
d'al-Albânî, verdict indicatif par les narrateurs, note /5 fournie et ce qu'elle signifie ; 4) Limites de l'analyse automatique."""


class QueryExpansion(BaseModel):
    language: str = Field(description="Langue de la question : fr, en ou ar")
    queries: list[str] = Field(description="4 à 6 requêtes de recherche (au moins 2 en arabe, 2 en anglais)")


@lru_cache(maxsize=1)
def _client() -> anthropic.Anthropic | None:
    """Client SDK (clé ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN ou profil `ant auth login`)."""
    try:
        c = anthropic.Anthropic()
    except (anthropic.AnthropicError, TypeError) as e:
        log.warning("LLM désactivé : %s", e)
        return None
    if not (c.api_key or c.auth_token or getattr(c, "credentials", None)):
        log.warning("LLM désactivé : aucune clé API Anthropic (ANTHROPIC_API_KEY) ni profil trouvé")
        return None
    return c


def available() -> bool:
    return settings.llm_enabled and _client() is not None


def expand_query(question: str) -> dict | None:
    c = _client()
    if c is None or not settings.llm_enabled:
        return None
    try:
        resp = c.messages.parse(
            model=settings.llm_model,
            max_tokens=1024,
            system=SYSTEM_EXPAND,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": question}],
            output_format=QueryExpansion,
        )
        if resp.stop_reason == "refusal" or resp.parsed_output is None:
            return None
        return resp.parsed_output.model_dump()
    except (anthropic.AuthenticationError, TypeError) as e:
        log.warning("authentification Anthropic impossible : expansion désactivée (%s)", e)
        return None
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
        log.warning("expansion LLM indisponible : %s", e)
        return None


def _compact(payload: dict) -> dict:
    """Réduit le JSON transmis au modèle à l'essentiel (limite la taille, garde la traçabilité)."""
    out = {"question": payload["question"], "hadiths": []}
    for r in payload["results"]:
        chains = []
        for c in r["chains"]:
            links = []
            for l in c["links"]:
                n = l["narrator"]
                links.append(
                    {
                        "name": l["name"],
                        "term": l["term"],
                        "narrator": None
                        if n is None
                        else {
                            "id": n["id"],
                            "name": n["name"],
                            "grade_label": n["grade_label_fr"],
                            "grade_ibn_hajar": n["grade_ibn_hajar"],
                            "grade_dhahabi": n["grade_dhahabi"],
                            "grade_text": n["grade_text"],
                            "tabaqa": n["tabaqa"],
                            "death_year_h": n["death_year_h"],
                            "match": l["match_method"],
                        },
                        "alternatives": [a["name"] for a in l["alternatives"]],
                    }
                )
            v = c["verdict"]
            chains.append({"links": links, "verdict": {"label_fr": v["label_fr"], "label_ar": v["label_ar"], "weakest": v["weakest"], "unresolved": v["unresolved"], "notes": v["notes"]}})
        out["hadiths"].append(
            {
                "id": r["id"],
                "reference": r["reference"],
                "collection_ar": r["collection_name_ar"],
                "chapter_ar": r["chapter_ar"],
                "grade_source_ar": r["grade_source_ar"],
                "grade_source_en": r["grade_source_en"],
                "isnad_ar": (r["isnad_ar"] or "")[:700],
                "matn_ar": (r["matn_ar"] or "")[:900],
                "matn_en": (r["matn_en"] or "")[:900],
                "chains": chains,
            }
        )
    return out


def synthesize(question: str, payload: dict) -> dict | None:
    """Mise en forme finale par Claude (sortie structurée : hadiths pertinents, synthèse, réponse).
    Refus / erreur / absence de clé -> None => réponse déterministe."""
    c = _client()
    if c is None or not settings.llm_enabled:
        return None
    data = json.dumps(_compact(payload), ensure_ascii=False)
    kwargs = dict(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        system=[{"type": "text", "text": SYSTEM_SYNTH, "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": f"Question : {question}\n\nDonnées (JSON) :\n{data}"}],
        output_format=SynthesisOutput,
    )
    try:
        try:  # repli serveur (safety classifiers) quand le SDK/l'API l'acceptent
            resp = c.beta.messages.parse(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
        except TypeError:
            resp = c.messages.parse(**kwargs)
        if resp.stop_reason == "refusal" or resp.parsed_output is None:
            log.warning("synthèse refusée ou vide (stop_reason=%s)", resp.stop_reason)
            return None
        out = resp.parsed_output.model_dump()
        valid = {r["id"] for r in payload["results"]}
        out["relevant_hadith_ids"] = [i for i in out["relevant_hadith_ids"] if i in valid]
        return out
    except (anthropic.AuthenticationError, TypeError) as e:
        log.warning("authentification Anthropic impossible : synthèse désactivée (%s)", e)
        return None
    except anthropic.RateLimitError as e:
        log.warning("limite de débit Anthropic : %s", e)
        return None
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
        log.warning("synthèse LLM indisponible : %s", e)
        return None


def summarize(results: list[dict]) -> dict[int, dict] | None:
    """Résumé bilingue d'une phrase par hadith (un seul appel). None si LLM indisponible."""
    c = _client()
    if c is None or not settings.llm_enabled or not results:
        return None
    items = [
        {"id": r["id"], "ar": (r.get("matn_ar") or r.get("text_ar") or "")[:600], "en": (r.get("matn_en") or r.get("text_en") or "")[:600]}
        for r in results
    ]
    try:
        resp = c.messages.parse(
            model=settings.llm_model,
            max_tokens=4000,
            system=SYSTEM_SUMMARY,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": json.dumps(items, ensure_ascii=False)}],
            output_format=SummaryBatch,
        )
        if resp.stop_reason == "refusal" or resp.parsed_output is None:
            return None
        return {it.id: {"ar": it.ar.strip(), "en": it.en.strip()} for it in resp.parsed_output.items}
    except (anthropic.AuthenticationError, TypeError) as e:
        log.warning("résumés LLM désactivés : %s", e)
        return None
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
        log.warning("résumés LLM indisponibles : %s", e)
        return None


def report_narrative(report: dict) -> str | None:
    """Rapport rédigé (français) pour un hadith. None si LLM indisponible."""
    c = _client()
    if c is None or not settings.llm_enabled:
        return None
    h = report["hadith"]
    compact = {
        "reference": h["reference"], "grade_source_ar": h["grade_source_ar"], "reliability": h.get("reliability"),
        "matn_ar": (h.get("matn_ar") or "")[:1200], "matn_en": (h.get("matn_en") or "")[:1200], "isnad_ar": (h.get("isnad_ar") or "")[:800],
        "chains": [
            {"verdict": c_["verdict"], "links": [
                {"name": l["name"], "term": l["term"], "match": l["match_method"],
                 "narrator": None if not l["narrator"] else {k: l["narrator"].get(k) for k in ("name", "grade_label_fr", "grade_ibn_hajar", "grade_dhahabi", "tabaqa", "death_year_h")}}
                for l in c_["links"]]}
            for c_ in h.get("chains", [])
        ],
        "opinions": {str(nid): [f"{o['critic']}: {o['opinion']}" for o in n.get("opinions", [])[:6]] for nid, n in report["narrators"].items()},
    }
    try:
        with c.messages.stream(
            model=settings.llm_model,
            max_tokens=3000,
            system=SYSTEM_REPORT,
            output_config={"effort": "medium"},
            messages=[{"role": "user", "content": json.dumps(compact, ensure_ascii=False)}],
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            return None
        return "".join(b.text for b in msg.content if b.type == "text").strip() or None
    except (anthropic.AuthenticationError, TypeError) as e:
        log.warning("rapport LLM désactivé : %s", e)
        return None
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
        log.warning("rapport LLM indisponible : %s", e)
        return None
