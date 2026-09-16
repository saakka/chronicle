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
