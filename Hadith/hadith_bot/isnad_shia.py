"""Parseur d'isnad pour les recueils imamites (al-Kāfī) : « علي بن إبراهيم عن أبيه عن ابن أبي عمير عن ... عن أبي عبد الله (عليه السلام) قال ».

Spécificités traitées :
  - la chaîne se termine sur un Imam ou le Prophète, repéré par la formule de vénération (عليه السلام، صلى الله عليه وآله)
  - « عدة من أصحابنا » : groupe de maîtres d'al-Kulaynī (maillon collectif)
  - « رفعه », « عمن ذكره », « عن رجل », « عن بعض أصحابنا » : maillon manquant / anonyme
  - « وعنه », « وبهذا الإسناد » : renvoi à la chaîne du hadith précédent
  - « جميعاً عن » : jonction de plusieurs voies
"""
from __future__ import annotations

import re

from .arabic import _ALEF, normalize_name, strip_tashkil
from .isnad import Chain, Link, _clean_name

# formules qui suivent le nom d'un Imam / du Prophète : tout ce qui précède est la chaîne
_INFALLIBLE_MARK = re.compile(
    r"\(?\s*(عليه السلام|عليها السلام|عليهم السلام|عليهما السلام|صل[يى] الله عليه و ?[اآ]له( وسلم)?|صلوات الله عليهم?ا?|سلام الله عليه)\s*\)?|\(\s*(ع|ص)\s*\)"
)
_WAW_NAMES = {"وهب", "وهيب", "وليد", "واصل", "وكيع", "واقد", "ورقاء", "وضاح", "وردان", "وابصه", "واثله", "وحشي", "وايل", "وهبان"}
_IMAM_HEADS_RAW = ("احدهما", "ابي عبد الله", "ابي جعفر", "ابي الحسن", "ابي ابراهيم", "ابي محمد", "ابا عبد الله", "ابا جعفر", "ابا الحسن", "ابا ابراهيم", "ابا محمد",
              "امير المومنين", "رسول الله", "النبي", "الرضا", "العبد الصالح", "الصادق", "الباقر", "الكاظم", "علي بن الحسين", "الحسن بن علي", "الحسين بن علي",
              "ابو عبد الله", "ابو جعفر", "ابو الحسن", "ابو ابراهيم", "ابو محمد", "صاحب الزمان", "القايم", "الحجه", "العسكري", "الهادي", "الجواد",
              "ابي الحسن الرضا", "ابي الحسن موسي", "ابي جعفر الثاني", "ابي الحسن الثالث", "ابي عبد الله جعفر", "جعفر بن محمد", "محمد بن علي الباقر", "موسي بن جعفر", "علي بن موسي")
IMAM_HEADS = tuple(sorted({normalize_name(h) for h in _IMAM_HEADS_RAW}, key=len, reverse=True))
TERMS = {"عن": "anana", "عمن": "anana", "حدثني": "sama", "حدثنا": "sama", "اخبرنا": "sama", "اخبرني": "sama", "سمعت": "sama", "سالت": "sama", "سال": "sama",
         "ذكر": "other", "كتبت": "other", "كتب": "other", "روي": "other", "رفعه": "marfu", "يرفعه": "marfu", "رفعوه": "marfu"}
UNNAMED = {"رجل", "رجلا", "بعض", "غير", "من", "عمن", "غيره", "قوم", "اصحابنا", "اصحابه", "رجال", "بعضهم", "بعضنا", "حدثه", "ذكره", "رواه", "اخبره", "سمعه", "حدثهم", "احد", "شيخ", "امراه"}
UNNAMED_PHRASES = ("عمن ذكره", "عمن حدثه", "عمن رواه", "عن رجل", "عن بعض اصحابنا", "عن بعض اصحابه", "عن غير واحد", "عن بعض", "عمن اخبره", "عن من ذكره")
GROUP_PHRASE = "عده من اصحابنا"
JOIN_WORDS = {"جميعا", "كلاهما", "كلهم", "ثلاثتهم"}
FLUSH = {"قال", "قالت", "قالا", "قالوا", "يقول", "انه", "انها", "و", "،", "انهما", "يذكر", "يحدث", "سالته", "سالتها", "قلت", "كتبت", "لي", "له", "لنا", "لهم"}
_PUNCT = re.compile(r"[؛؟\.,;:!\?\"'«»\[\]\{\}\-–—ـ]+")
_WS = re.compile(r"\s+")
_NUM_PREFIX = re.compile(r"^\s*\d+\s*[-ـ–]?\s*")
_KUNYA_START = ("ابو", "ابي", "ابا", "ابن", "ام", "عبد", "محمد", "علي", "احمد", "الحسن", "الحسين", "جعفر", "موسي", "سهل", "يونس", "حماد", "صفوان", "ابان", "هشام", "زراره", "بريد", "معاويه", "عبيد", "اسحاق", "اسماعيل", "ابراهيم", "يحيي", "يعقوب", "الفضل", "فضاله", "حريز", "منصور", "عاصم", "داود", "سليمان", "عثمان", "عمر", "عمرو", "سعد", "سعيد", "جميل", "مالك", "المفضل", "الوليد", "النضر", "القاسم", "خالد", "زياد", "حفص", "ثعلبه", "عمار", "سماعه", "زكريا", "بكر", "غير")


def prepare_shia(text: str) -> tuple[str, str | None, int]:
    """Retire tashkil et numéro ; renvoie (texte normalisé, position de la formule de vénération, index de coupe)."""
    s = strip_tashkil(text)
    s = _NUM_PREFIX.sub("", s)
    s = _ALEF.sub("ا", s)
    s = s.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    m = _INFALLIBLE_MARK.search(s)
    return s, (m.group(0) if m else None), (m.start() if m else -1)


def _tokens(seg: str) -> list[str]:
    seg = _PUNCT.sub(" ", seg).replace("،", " ، ").replace("(", " ").replace(")", " ")
    return [t for t in _WS.sub(" ", seg).split() if t]


def _is_term(tok: str) -> str | None:
    if tok in TERMS:
        return tok
    if tok[:1] in ("و", "ف") and tok[1:] in TERMS:
        return tok[1:]
    return None


def _make(name: str, term: str | None, *, imam: bool = False, group: bool = False, unnamed: bool = False, marfu: bool = False) -> Link:
    l = Link(name=name, name_norm=normalize_name(name), term=term, mode=TERMS.get(term) if term else None)
    l.is_relative = name.split()[0] in {"ابيه", "ابيها", "جده", "امه", "عمه", "اخيه"} if name else False
    l.kind = "imam" if imam else "group" if group else "unnamed" if unnamed else "marfu" if marfu else "relative" if l.is_relative else "normal"
    l.is_unnamed = unnamed
    return l


def parse_isnad_shia(text_ar: str | None, prev_links: list[Link] | None = None) -> tuple[list[Chain], str]:
    """Renvoie (chaînes, matn) ; `prev_links` = maillons du hadith précédent (pour « وعنه » / « وبهذا الإسناد »)."""
    if not text_ar:
        return [], ""
    s, mark, cut = prepare_shia(text_ar)
    if cut >= 0:
        chain_text, matn = s[:cut], s[cut + len(mark or "") :].strip()
        imam_present = True
    else:
        # pas de formule : on coupe au premier « قال » narratif après au moins deux maillons
        m = re.search(r"\bقال (قال|سمعت|سالت|كان|ان|اذا|لما|كنت|دخلت|من)\b|\bيقول\b|\bقالت\b", s)
        chain_text, matn = (s[: m.start()], s[m.start() :]) if m else (s[:220], s[220:])
        imam_present = False
    toks = _tokens(chain_text)
    links: list[Link] = []
    cur: list[str] = []
    term: str | None = None
    join_at: int | None = None
    after_sep = False
    marfu_flag = False
    prev_links = [l for l in (prev_links or []) if getattr(l, "kind", "normal") != "imam"]

    def flush(*, coordinated: bool = False) -> None:
        nonlocal cur
        words = list(cur)
        cur = []
        name = _clean_name(words)
        if not name:
            if term == "عمن" and words:  # « عمن حدثه » : maillon anonyme
                links.append(_make("عمن " + " ".join(words), term, unnamed=True))
            return
        nn = normalize_name(name)
        if nn.startswith(GROUP_PHRASE) or nn == "عده":
            links.append(_make("عدة من أصحابنا", term, group=True))
            return
        head = nn.split()[0]
        if head in UNNAMED or any(nn.startswith(p.split(" ", 1)[1]) for p in UNNAMED_PHRASES if " " in p):
            links.append(_make(name, term, unnamed=True))
            return
        link = _make(name, term)
        if coordinated and links:
            link.term, link.mode = links[-1].term, links[-1].mode
            links[-1].alternatives.append(link)
        else:
            links.append(link)

    i = 0
    # renvois au hadith précédent
    if toks[:2] == ["و", "بهذا"] or toks[:1] == ["وبهذا"] or toks[:1] == ["بهذا"]:
        links.extend(_copy(l) for l in prev_links)
        while i < len(toks) and toks[i] not in ("الاسناد", "الإسناد"):
            i += 1
        i += 1
    elif toks[:1] in (["وعنه"], ["عنه"]) and prev_links:
        links.append(_copy(prev_links[0]))
        i = 1
        term = "عن"
    while i < len(toks):
        tok = toks[i]
        t = _is_term(tok)
        if t:
            flush()
            if TERMS[t] == "marfu":
                marfu_flag = True
                links.append(_make("رفعه (maillon omis)", t, marfu=True))
                term = None
            else:
                term = t
            after_sep = False
        elif tok == "،":
            flush()
            after_sep = True
        elif tok in JOIN_WORDS:
            flush()
            join_at = len(links)
        elif tok in FLUSH:
            if tok == "و":
                if cur:
                    flush()
                after_sep = True
            else:
                flush()
        elif tok in ("وغيره", "وغيرهما", "وغيرهم"):
            flush()
            if links:
                links[-1].alternatives.append(_make("غيره", links[-1].term, unnamed=True))
        else:
            if tok.startswith("و") and len(tok) > 2 and tok not in _WAW_NAMES and (cur or after_sep or links) and (tok[1:].startswith(_KUNYA_START) or (cur and cur[-1] not in ("بن", "ابي", "ابو", "ام", "ابن"))):
                if cur:
                    flush()
                cur = [tok[1:]]
                i += 1
                while i < len(toks) and not _is_term(toks[i]) and toks[i] not in FLUSH and toks[i] not in JOIN_WORDS:
                    cur.append(toks[i])
                    i += 1
                flush(coordinated=True)
                after_sep = False
                continue
            cur.append(tok)
            after_sep = False
        i += 1
    flush()
    # dernier maillon = l'Imam / le Prophète : nom repéré par sa kunya, juste avant la formule de vénération
    def _imam_of(nn: str) -> bool:
        nn = nn[1:] if nn.startswith("ل") and not nn.startswith("لل") else nn
        return any(nn.startswith(h) for h in IMAM_HEADS)

    if links and _imam_of(links[-1].name_norm):
        links[-1].kind = "imam"
        if links[-1].name_norm.startswith("ل"):
            links[-1].name = links[-1].name[1:]
            links[-1].name_norm = links[-1].name_norm[1:]
    elif imam_present:
        tail = [t for t in _tokens(chain_text)[-5:] if t not in FLUSH]
        for k in range(len(tail)):
            cand = normalize_name(" ".join(tail[k:]))
            if _imam_of(cand):
                name = " ".join(tail[k:])
                if name.startswith("ل") and not name.startswith("لل"):
                    name = name[1:]
                if not links or links[-1].name_norm != normalize_name(name):
                    links.append(_make(name, "عن", imam=True))
                else:
                    links[-1].kind = "imam"
                break
    for k, l in enumerate(links):
        l.position = k
    chains = [Chain(links=links, raw=chain_text.strip())]
    if join_at is not None and 0 < join_at < len(links):
        chains[0].join_inferred = False
    return chains, matn


def _copy(l: Link) -> Link:
    n = Link(name=l.name, name_norm=l.name_norm, term=l.term, mode=l.mode, is_relative=l.is_relative, is_unnamed=l.is_unnamed)
    n.kind = getattr(l, "kind", "normal")
    return n
