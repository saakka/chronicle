"""Modèle de langage local (MLX, Apple Silicon) : compréhension de la question, pertinence,
extraction des réponses, résumés et synthèse. Aucune API externe. Le modèle ne note jamais :
les notes /5 restent calculées par `grading` à partir des jugements en base."""
from __future__ import annotations

import json
import logging
import re
import threading
from functools import lru_cache

from .config import settings

log = logging.getLogger(__name__)
_LOCK = threading.Lock()  # une génération à la fois (GPU partagé)


@lru_cache(maxsize=1)
def _model():
    from mlx_lm import load

    log.info("chargement du modèle local %s", settings.local_model)
    return load(settings.local_model)


def available() -> bool:
    if settings.llm_backend != "local":
        return False
    try:
        import mlx_lm  # noqa: F401
    except ImportError:
        return False
    try:
        from huggingface_hub import try_to_load_from_cache

        return try_to_load_from_cache(settings.local_model, "config.json") is not None
    except Exception:
        return True


def warm_up() -> None:
    try:
        _model()
    except Exception as e:  # pragma: no cover
        log.warning("modèle local indisponible : %s", e)


def chat(system: str, user: str, *, max_tokens: int = 800, temp: float = 0.0) -> str:
    from mlx_lm import generate

    model, tok = _model()
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    kwargs: dict = {"max_tokens": max_tokens, "verbose": False}
    try:
        from mlx_lm.sample_utils import make_sampler

        kwargs["sampler"] = make_sampler(temp=temp)
    except Exception:  # anciennes versions
        kwargs["temp"] = temp
    with _LOCK:
        return generate(model, tok, prompt=prompt, **kwargs)


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def _extract_json(txt: str):
    m = _FENCE.search(txt)
    if m:
        txt = m.group(1)
    txt = txt.strip()
    # on part du premier délimiteur rencontré (une liste peut contenir des objets)
    pairs = sorted(((txt.find(o), o, c) for o, c in (("{", "}"), ("[", "]")) if txt.find(o) != -1), key=lambda t: t[0])
    for i, opener, closer in pairs:
        j = txt.rfind(closer)
        if opener == "[" and j < i:  # liste ouverte jamais fermée : sortie tronquée
            return _salvage_list(txt)
        if j > i:
            try:
                return json.loads(txt[i : j + 1])
            except json.JSONDecodeError:
                continue
    return _salvage_list(txt)


def _salvage_list(txt: str):
    """Liste JSON tronquée par max_tokens : on garde les objets complets déjà émis."""
    i = txt.find("[")
    if i == -1:
        return None
    out, depth, start, in_str, esc = [], 0, None, False, False
    for k in range(i + 1, len(txt)):
        ch = txt[k]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = k
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    out.append(json.loads(txt[start : k + 1]))
                except json.JSONDecodeError:
                    pass
                start = None
    return out or None


def chat_json(system: str, user: str, *, max_tokens: int = 800, retry: bool = True):
    """Génération contrainte à du JSON (une relance si invalide et non tronqué)."""
    sys_ = system + "\nRespond with valid JSON only. No prose, no markdown fences. Arabic without diacritics (no tashkil)."
    out = chat(sys_, user, max_tokens=max_tokens)
    obj = _extract_json(out)
    if obj is None and retry and len(out) < max_tokens * 2:  # sortie courte et invalide -> une relance ; tronquée -> inutile
        out = chat(sys_, user + "\n\nYour previous output was not valid JSON. Output the JSON only.", max_tokens=max_tokens)
        obj = _extract_json(out)
    if obj is None:
        log.warning("JSON invalide du modèle local : %s", out[:200])
    return obj


# ------------------------------------------------------------------------------------------------
SYS_UNDERSTAND = """You are a research assistant specialised in hadith (the six canonical Sunni collections) and Islamic history.
Given a user question in Arabic, French or English, infer what the user most likely wants to find, as a knowledgeable scholar
would, then produce search phrases. The Arabic phrases must imitate the WORDING OF THE HADITH TEXTS themselves (first-person
narration, e.g. "تزوجني رسول الله وانا بنت", "قال رسول الله", "كنت مع النبي", "توفي النبي وانا ابن"), never a paraphrase of the
question. English phrases must use the wording of the classical translations. No diacritics. Output JSON exactly like the examples.
Example 1 — Q: "combien de rak'a le Prophète priait la nuit ?"
{"language": "fr", "intent": "fact", "question_en": "How many rak'ahs did the Prophet pray at night?", "question_ar": "كم ركعة كان النبي يصلي بالليل؟",
 "looking_for": "le nombre de rak'a de la prière de nuit du Prophète",
 "queries_ar": ["ما كان يزيد في رمضان ولا في غيره على احدى عشرة ركعة", "يصلي من الليل ثلاث عشرة ركعة", "صلاة الليل مثنى مثنى"],
 "queries_en": ["never exceeded eleven rakat in Ramadan or otherwise", "used to pray thirteen rakat at night"]}
Example 2 — Q: "كم كان عمر ابن عباس عند وفاة النبي"
{"language": "ar", "intent": "fact", "question_en": "How old was Ibn Abbas when the Prophet died?", "question_ar": "كم كان عمر ابن عباس عند وفاة النبي؟",
 "looking_for": "عمر ابن عباس يوم توفي النبي",
 "queries_ar": ["توفي رسول الله وانا ابن عشر سنين", "قبض النبي وانا ختين", "توفي النبي وانا ابن خمس عشرة"],
 "queries_en": ["the Prophet died when I was ten years old", "at the time of the Prophet's death I was circumcised"]}
Example 3 — Q: "who was the first to accept Islam"
{"language": "en", "intent": "fact", "question_en": "Who was the first person to accept Islam?", "question_ar": "من اول من اسلم؟",
 "looking_for": "the name of the first person to embrace Islam",
 "queries_ar": ["اول من اسلم", "اول من صلى مع رسول الله", "اسلم ابو بكر"],
 "queries_en": ["the first to embrace Islam", "the first to accept Islam was"]}"""

SYS_TRIAGE = """You are a hadith research assistant. The user asked a question; you receive candidate hadiths (id, Arabic text,
English translation). Decide for each whether it actually contains information answering the question (not merely the same topic).
Output a JSON list of the ids of the relevant hadiths only, e.g. [12, 40]. Output [] if none."""

SYS_EXTRACT = """You are a hadith research assistant. For each hadith given (id, Arabic text, English translation), extract the
answer it gives to the question. Use only what the text says; never invent. Output a JSON list, one object per hadith, same order:
[{"id": <id>,
  "answer": "<= 20 words, in the question's language, the answer exactly as the hadith states it, with every value it mentions (e.g. 'تزوجها وهي بنت ست، وبنى بها وهي بنت تسع')",
  "answer_key": "very short normalized label to group identical answers, e.g. '6 / 9', 'yes', 'Abu Bakr'",
  "summary_ar": "<= 15 Arabic words: what the hadith is about",
  "summary_en": "<= 15 English words: what the hadith is about"}]
Arabic without diacritics."""

SYS_GROUP = """You receive a question and a list of answers extracted from individual hadiths (id, answer, answer_key).
Merge answers that say the same thing into distinct answer groups (do not merge answers that give different values).
Output a JSON list ordered by number of supporting hadiths, descending:
[{"answer": "the answer in the question's language", "answer_ar": "the same in Arabic", "answer_en": "the same in English", "ids": [ids]}]"""

SYS_SYNTH = """You are a hadith research assistant. Write 2 to 4 sentences, in the language of the question, that answer it using ONLY
the answer groups provided (each has a reliability score /5 computed by the system and its sources). Mention the sources by
reference (e.g. Sahih al-Bukhari n°3894). Do not add facts, do not give a fatwa, do not invent scores. Plain text, no JSON."""


def understand(question: str) -> dict | None:
    obj = chat_json(SYS_UNDERSTAND, f"Q: {question}", max_tokens=500)
    if not isinstance(obj, dict):
        return None
    obj["queries_ar"] = [q for q in (obj.get("queries_ar") or []) if isinstance(q, str) and q.strip()][:5]
    obj["queries_en"] = [q for q in (obj.get("queries_en") or []) if isinstance(q, str) and q.strip()][:4]
    return obj


def _items(results: list[dict], n: int = 450) -> list[dict]:
    return [{"id": r["id"], "ar": (r.get("matn_ar") or r.get("text_ar") or "")[:n], "en": (r.get("matn_en") or r.get("text_en") or "")[:n]} for r in results]


def triage(question: str, looking_for: str | None, results: list[dict]) -> list[int]:
    """Ids des hadiths qui répondent réellement à la question (sortie très courte, donc rapide)."""
    if not results:
        return []
    user = f"Question: {question}\nLooking for: {looking_for or ''}\n\nHadiths:\n{json.dumps(_items(results), ensure_ascii=False)}"
    obj = chat_json(SYS_TRIAGE, user, max_tokens=120)
    valid = {r["id"] for r in results}
    if isinstance(obj, dict):
        obj = obj.get("ids") or obj.get("relevant") or []
    if not isinstance(obj, list):
        return []
    return [int(i) for i in obj if str(i).lstrip("-").isdigit() and int(i) in valid]


def extract(question: str, looking_for: str | None, results: list[dict], batch: int = 4) -> dict[int, dict]:
    """Réponse + résumés ar/en pour chaque hadith pertinent (par lots courts : sorties fiables)."""
    out: dict[int, dict] = {}
    for i in range(0, len(results), batch):
        chunk = results[i : i + batch]
        user = f"Question: {question}\nLooking for: {looking_for or ''}\n\nHadiths:\n{json.dumps(_items(chunk, 600), ensure_ascii=False)}"
        obj = chat_json(SYS_EXTRACT, user, max_tokens=190 * len(chunk) + 80, retry=False)
        if isinstance(obj, dict):
            obj = [obj]
        if isinstance(obj, list):
            for it in obj:
                if isinstance(it, dict) and str(it.get("id", "")).lstrip("-").isdigit():
                    out[int(it["id"])] = it
    return out


_AR_NUM = {"واحد": 1, "واحده": 1, "اثنين": 2, "اثنتين": 2, "ثلاث": 3, "ثلاثه": 3, "اربع": 4, "اربعه": 4, "خمس": 5, "خمسه": 5, "ست": 6, "سته": 6,
           "سبع": 7, "سبعه": 7, "ثمان": 8, "ثماني": 8, "ثمانيه": 8, "تسع": 9, "تسعه": 9, "عشر": 10, "عشره": 10, "عشرين": 20, "ثلاثين": 30, "اربعين": 40,
           "خمسين": 50, "ستين": 60, "سبعين": 70, "ثمانين": 80, "تسعين": 90, "مايه": 100, "ماية": 100, "الف": 1000}
_FR_NUM = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "treize": 13,
           "vingt": 20, "trente": 30, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
           "twelve": 12, "thirteen": 13, "twenty": 20, "thirty": 30}


def _num_signature(text: str) -> str:
    """Suite des nombres cités (chiffres ou mots ar/fr/en) : « بنت ست ... بنت تسع » -> « 6 9 »."""
    from .arabic import normalize

    nums: list[str] = []
    for tok in re.findall(r"[\w\u0600-\u06FF]+", normalize(text).lower()):
        if tok.isdigit():
            nums.append(tok)
            continue
        cands = [tok]
        for pre in ("وال", "فال", "بال", "كال", "ال", "و", "ف", "ل", "ب", "ك"):  # « لسبعة », « وتسع », « بثلاث »
            if tok.startswith(pre) and len(tok) > len(pre) + 1:
                cands.append(tok[len(pre):])
        for c in cands:
            if c in _AR_NUM:
                nums.append(str(_AR_NUM[c]))
                break
            if c in _FR_NUM:
                nums.append(str(_FR_NUM[c]))
                break
    # « ثمان عشرة » = 18 : on fusionne unité + عشر(ة)
    out: list[str] = []
    for n in nums:
        if out and n == "10" and out[-1].isdigit() and int(out[-1]) < 10:
            out[-1] = str(int(out[-1]) + 10)
        else:
            out.append(n)
    return " ".join(out)


def verify_claim(claim: dict, matn: str | None) -> dict:
    """Contrôle anti-invention : chaque nombre cité dans la réponse extraite doit figurer dans le texte
    du hadith. Sinon la réponse est marquée non vérifiée et les nombres du texte font foi."""
    answer_nums = _num_signature(claim.get("answer") or "").split()
    if not answer_nums:
        claim["verified"] = True
        claim["sig"] = ""
        return claim
    if matn is None:  # pas de texte de référence : invérifiable, on garde les nombres de la réponse
        claim["verified"] = True
        claim["sig"] = " ".join(answer_nums[:2])
        return claim
    text_nums = _num_signature(matn).split()
    ok = [n for n in answer_nums if n in text_nums]
    claim["verified"] = len(ok) == len(answer_nums)
    # réponse non conforme au texte -> ce sont les nombres du texte qui classent le hadith
    claim["sig"] = " ".join((answer_nums if claim["verified"] else text_nums)[:2])
    return claim


def group(question: str, claims: list[dict]) -> list[dict]:
    """Regroupement déterministe des réponses : mêmes nombres (vérifiés dans le texte), sinon même étiquette.
    (Un petit modèle fusionne à tort « 6 / 9 » et « 7 / 9 » : on ne lui confie pas cette étape.)"""
    if not claims:
        return []
    from .arabic import normalize

    buckets: dict[str, list[dict]] = {}
    for c in claims:
        if "sig" not in c:
            verify_claim(c, c.get("matn"))
        # les deux premiers nombres portent la réponse (« 6 / 9 ») ; les suivants sont des détails (« … بنت ثمان عشرة »)
        key = c["sig"] or normalize(c.get("answer_key") or "").lower() or normalize(c.get("answer") or "").lower()
        buckets.setdefault(key, []).append(c)
    groups = []
    for key, members in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        texts = [m["answer"] for m in members if m.get("answer") and m.get("verified", True)] or [m["answer"] for m in members if m.get("answer")]
        # libellé : la formulation vérifiée la plus fréquente, à défaut la plus courte
        best = max(set(texts), key=lambda t: (texts.count(t), -len(t))) if texts else key
        groups.append({"answer": best, "answer_ar": "", "answer_en": "", "ids": [m["id"] for m in members],
                       "unverified_ids": [m["id"] for m in members if not m.get("verified", True)]})
    return groups
