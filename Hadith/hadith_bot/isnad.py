"""Extraction de la chaîne de transmission (isnad) : « حدثنا فلان عن فلان عن فلان ... ».

Le parseur travaille sur le texte arabe débarrassé du tashkil et produit, pour chaque chaîne,
une liste de maillons ordonnés du maître du compilateur vers le Compagnon. Il gère :
  - les termes de transmission (حدثنا، أخبرنا، عن، سمعت، أن، ...) et leur mode (samâ' / 'an'ana)
  - le تحويل (« ح ») qui ouvre une seconde chaîne, avec jonction explicite (« كلاهما عن ») ou inférée
  - les co-rapporteurs d'un même niveau (« حدثنا فلان وفلان قالا ... »)
  - les références relatives (« عن أبيه », « عن جده ») signalées comme telles
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .arabic import _ALEF, _HONORIFIC_RE, normalize_name, strip_tashkil

# terme normalisé -> mode de transmission
TERMS: dict[str, str] = {
    "حدثنا": "sama", "حدثني": "sama", "حدثناه": "sama", "حدثنيه": "sama", "حدثه": "sama", "حدثهم": "sama",
    "ثنا": "sama", "نا": "sama", "دثنا": "sama",
    "اخبرنا": "sama", "اخبرني": "sama", "اخبرناه": "sama", "اخبره": "sama", "اخبرهم": "sama", "انا": "sama",
    "انبانا": "sama", "انباني": "sama", "انباه": "sama", "ابنا": "sama",
    "سمعت": "sama", "سمع": "sama", "سمعنا": "sama",
    "عن": "anana",
    "ان": "an",
    "قرات": "sama", "قري": "sama", "كتب": "other", "بلغني": "other", "ذكر": "other", "رايت": "other",
}
JOIN_WORDS = {"كلاهما", "كليهما", "كلهم", "جميعا", "ثلاثتهم", "اربعتهم", "خمستهم"}
FLUSH_WORDS = {"قال", "قالا", "قالوا", "يقول", "قالت", "يحدث", "تحدث", "يذكر", "انه", "انها", "انهما", "و", "،", "ح", "واللفظ", "لفظ", "المعني", "بمعناه", "نحوه", "مثله", "بهذا", "الاسناد", "بمثله", "بنحوه"}
RELATIVE_HEADS = {"ابيه", "ابيها", "اباه", "جده", "جدها", "امه", "امها", "عمه", "عمها", "اخيه", "اخيها", "خاله", "جدته", "عمته", "خالته", "ابنه", "مولاه", "مولاته", "زوجه", "زوجها"}
RELATIVE_SINGLE = {"ابي", "جدي", "امي", "عمي", "اخي", "خالي", "ابنه"}
STOP_HEADS = {"رسول", "النبي", "نبي", "الله"}
_UNNAMED = {"رجل", "شيخ", "امراه", "بعض", "غير", "من", "ناس", "رجلا", "رجلين", "اناس", "قوم", "رجال", "غيره", "اخر", "شيخا", "رجالا"}
# mots de liaison / contexte narratif : coupent le nom (« عائشة زوج النبي », « أبي سعيد قال له », « على المنبر »)
CONTEXT_CUT = {"علي", "في", "عند", "يوم", "بين", "حين", "لما", "بعد", "قبل", "وهو", "وهي", "وهم", "انه", "انها", "ونحن", "بمكه", "بالمدينه", "بالكوفه", "بالبصره",
               "له", "لهم", "لها", "كان", "كانت", "هذا", "ما", "واحد", "غير", "وغير", "وقال", "قال", "قالت", "كل", "هولاء", "اسمع", "وانا", "قراءه", "عليه", "اخبرته", "اخبرتني",
               "زوج", "زوجه", "ذكر", "بهذا", "الاسناد", "مثله", "نحوه", "بمثله", "بنحوه", "جميعا", "المعني", "واللفظ", "لفظ", "يخطب", "يحدث", "بذلك", "به", "عنه", "عنها", "عنهم", "عنهما",
               "اليه", "فيه", "منه", "ثم", "اذ", "اذا", "حتي", "الي", "الا", "انا", "نحن", "هم", "يقول", "تقول", "يحدثه", "تحدثه", "خطب", "سال", "سالت", "ساله", "سمعته", "سمعتها", "فقال", "فقالت",
               "دخل", "دخلنا", "فسالهم", "فساله", "فسالت", "فسال", "ذاك", "ذلك", "جاء", "جاءت", "اتي", "اتيت", "خرج", "خرجنا", "رايت", "كنا", "كانوا", "بينما", "بينا"}
# têtes de nom incomplètes : une virgule parasite du corpus ne doit pas couper « وابن، سيرين »
INCOMPLETE_HEADS = {"بن", "ابن", "ابو", "ابي", "ابا", "ام", "عبد", "بنت", "مولي", "عبدالله", "عبيدالله", "ال"}
GLUE_WORDS = {"هو", "وهو", "هي", "وهي", "يعني", "اعني"}
# mots de tête à retirer (« سألت عائشة » -> « عائشة » ; « وقال الآخران » -> rien)
LEADING_STRIP = (CONTEXT_CUT - {"علي"}) | {"و", "،", "وقال", "وقالا", "وقالوا", "فقال", "سالت", "سال", "لي", "لنا", "له", "لهم", "سالته", "قلت", "دخلت", "كنت", "سمعه", "يخبر", "وكان", "او", "فيما", "وهذا", "حدثته", "باسناده",
                                             "الحديث", "اخبراه", "اخبرني", "اخبرنا", "الاخران", "الاخرون", "الاخر", "قلت", "قال", "فحدثني", "فحدثنا", "ثم", "بعد", "ان",
                                             "حدثاه", "حدثه", "وغيره", "من", "لفظه", "ومعناه", "حديثه", "معناه", "ولفظه",
                                             "دخل", "دخلنا", "فسالهم", "فساله", "فسالت", "فسال", "ذاك", "ذلك", "جاء", "جاءت", "اتي", "اتيت", "خرج", "خرجنا", "رايت", "كنا", "كانوا", "بينما", "بينا"}
# « واللفظ لابن المثنى » / « الحديث لفلان » : attribution du wording, pas un maillon
WORDING_WORDS = {"واللفظ", "اللفظ", "لفظ", "لفظه", "ولفظه", "والسياق", "وسياق", "الحديث", "والحديث", "حديثه", "بمعني", "والمعني", "المعني", "ومعناه", "معناه"}
NAME_STARTS = ("ابو", "ابن", "ابي", "ام", "عبد", "محمد", "احمد", "يحيي", "علي", "الحسن", "الحسين", "زهير", "اسحاق", "قتيبه", "هناد", "عثمان", "عمرو", "عمر", "سعيد", "سفيان", "شعبه", "مالك", "وكيع", "هشام", "هارون", "عبيد", "ابراهيم", "اسماعيل", "موسي", "يعقوب", "يوسف", "زياد", "بشر", "بكر", "حجاج", "حماد", "خالد", "داود", "روح", "سليمان", "شيبان", "صالح", "طلحه", "عاصم", "عباد", "عفان", "عمران", "غندر", "فضيل", "قاسم", "كثير", "ليث", "مجاهد", "محمود", "مسدد", "معاذ", "معاويه", "منصور", "نصر", "هاشم", "وهب", "يزيد", "يونس", "جرير", "جعفر", "حفص", "حميد", "زكريا", "زيد", "سلمه", "سهل", "شريك", "عبده", "عيسي", "قيس", "مسلم", "معمر", "مغيره", "نافع", "همام", "الاعمش", "الزهري", "الليث", "الوليد", "المغيره", "الاوزاعي", "الثوري", "النضر", "الحكم", "الحميدي", "التميمي", "العلاء", "الفضل", "الاسود", "الحارث", "الربيع", "القاسم", "المثني", "المسيب", "النعمان", "محرز", "بندار", "ابان", "ايوب", "بشار", "حرمله", "خلف", "سويد", "عبدالله", "عبدالرحمن", "عبيدالله", "عمرو", "هدبه", "يعلي", "الحكم", "العباس", "الوليد")

PROPHET_RE = re.compile(r"\b(رسول الله|النبي|نبي الله)\b")
_PUNCT_KEEP_COMMA = re.compile(r"[؛؟\.,;:!\?\"'«»\(\)\[\]\{\}\-–—ـ]+")
_WS = re.compile(r"\s+")


@dataclass
class Link:
    name: str  # nom tel qu'écrit (sans tashkil)
    name_norm: str  # forme canonique pour l'appariement
    term: str | None  # terme de transmission qui précède le nom
    mode: str | None  # sama | anana | an | other
    is_relative: bool = False
    is_unnamed: bool = False  # « رجل », « شيخ » ...
    position: int = 0
    inferred: bool = False  # maillon hérité d'une autre chaîne (jonction inférée après « ح »)
    kind: str = "normal"  # normal | relative | unnamed | group | marfu | imam
    alternatives: list["Link"] = field(default_factory=list)  # co-rapporteurs au même niveau


@dataclass
class Chain:
    links: list[Link]
    raw: str
    join_inferred: bool = False


def prepare(isnad_ar: str) -> str:
    """Normalisation dédiée : garde la virgule arabe (frontière de nom)."""
    s = strip_tashkil(isnad_ar)
    s = _HONORIFIC_RE.sub(" ", s)
    s = _ALEF.sub("ا", s)
    s = s.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    s = _PUNCT_KEEP_COMMA.sub(" ", s)
    s = s.replace("،", " ، ")
    return _WS.sub(" ", s).strip()


def _is_term(tok: str) -> str | None:
    if tok in TERMS:
        return tok
    if tok[:1] in ("و", "ف") and tok[1:] in TERMS:  # « وحدثنا », « فأخبرنا »
        return tok[1:]
    return None


def _clean_name(words: list[str]) -> str:
    if words and words[0] in WORDING_WORDS:
        return ""
    words = [w for w in words if w not in GLUE_WORDS]
    while words and words[-1] in {"انه", "انها", "قال", "قالت", "يقول", "و", "،", "انهما"}:
        words.pop()
    while words and words[0] in LEADING_STRIP:
        words.pop(0)
    if words and words[0].startswith("ل") and (words[0][1:] in INCOMPLETE_HEADS or words[0][1:].startswith("ابن") or words[0][1:].startswith("ابي")):
        return ""  # « لابن المثنى », « لأبي بكر » : destinataire du wording
    # coupe le contexte narratif / les mots de liaison après le nom
    for i in range(1, len(words)):
        w = words[i]
        if w in CONTEXT_CUT and words[i - 1] not in {"بن", "ابن", "ابي", "ابو", "ام", "مولي", "بنت", "عبد"}:
            words = words[:i]
            break
    if words and all(w in CONTEXT_CUT or w in {"و", "،"} for w in words):
        return ""
    return " ".join(words)


def parse_isnad(isnad_ar: str | None, matn_ar: str | None = None) -> list[Chain]:
    """Renvoie une liste de chaînes (plusieurs en cas de تحويل « ح »).

    `matn_ar` sert à compléter un dernier nom tronqué par la segmentation du corpus
    (« عن جابر بن عبد » + matn « الله قال ... »)."""
    if not isnad_ar:
        return []
    text = prepare(isnad_ar)
    if matn_ar:
        last = text.rstrip(" ،").split()
        if last and last[-1] in INCOMPLETE_HEADS:
            extra = []
            for tok in prepare(matn_ar).split()[:4]:
                if _is_term(tok) or tok in FLUSH_WORDS or tok in CONTEXT_CUT or tok == "،":
                    break
                extra.append(tok)
                if tok not in INCOMPLETE_HEADS:
                    break
            text = text.rstrip(" ،") + " " + " ".join(extra)
    m = PROPHET_RE.search(text)
    if m:
        text = text[: m.start()]
    segments = [s.strip() for s in re.split(r"(?:^|\s)ح(?:\s|$)", text) if s.strip()]
    parsed: list[tuple[list[Link], int | None, str]] = []
    for seg in segments:
        links, join_at = _parse_segment(seg)
        if links:
            parsed.append((links, join_at, seg))
    if not parsed:
        return []
    # jonction des chaînes après تحويل
    chains: list[Chain] = []
    last_links, last_join, _ = parsed[-1]
    if last_join is not None and last_join < len(last_links):
        shared = last_links[last_join:]
        own_last = last_links[:last_join]
        for links, _, raw in parsed[:-1]:
            chains.append(Chain(links=links + [_copy(l, inferred=False) for l in shared], raw=raw))
        chains.append(Chain(links=own_last + shared, raw=parsed[-1][2]))
    else:
        for links, _, raw in parsed[:-1]:
            tail = [_copy(l, inferred=True) for l in last_links[len(links):]]
            chains.append(Chain(links=links + tail, raw=raw, join_inferred=bool(tail)))
        chains.append(Chain(links=last_links, raw=parsed[-1][2]))
    for c in chains:
        for i, l in enumerate(c.links):
            l.position = i
    return chains


def _copy(l: Link, *, inferred: bool) -> Link:
    return Link(name=l.name, name_norm=l.name_norm, term=l.term, mode=l.mode, is_relative=l.is_relative,
                is_unnamed=l.is_unnamed, inferred=inferred or l.inferred, alternatives=list(l.alternatives))


def _make_link(name: str, term: str | None) -> Link | None:
    head = name.split()[0]
    if head in STOP_HEADS:
        return None
    return Link(
        name=name,
        name_norm=normalize_name(name),
        term=term,
        mode=TERMS.get(term) if term else None,
        is_relative=head in RELATIVE_HEADS or name in RELATIVE_SINGLE,
        is_unnamed=head in _UNNAMED,
    )


def _parse_segment(seg: str) -> tuple[list[Link], int | None]:
    toks = seg.split()
    links: list[Link] = []
    cur: list[str] = []
    cur_term: str | None = None
    after_sep = False
    join_at: int | None = None

    def flush(*, coordinated: bool = False, final: bool = False) -> None:
        nonlocal cur
        if cur and not final and cur[-1] in INCOMPLETE_HEADS and all(w in INCOMPLETE_HEADS for w in cur):
            return  # « وابن، سيرين » : virgule parasite, on continue d'accumuler
        appendix = bool(cur) and cur[0] in GLUE_WORDS and bool(links) and not coordinated
        name = _clean_name(cur)
        cur = []
        if not name:
            return
        head = name.split()[0]
        if head.startswith("ل") and len(head) > 2 and (head[1:].startswith(NAME_STARTS) or any(l.name.split()[0] == head[1:] for l in links)):
            return  # « واللفظ لزهير » : attribution du wording à un maillon déjà cité
        if appendix:  # « حاتم، يعني ابن إسماعيل » : précision du nom précédent
            prev = links[-1].alternatives[-1] if links[-1].alternatives else links[-1]
            prev.name = f"{prev.name} {name}"
            prev.name_norm = normalize_name(prev.name)
            return
        if cur_term == "قرات" and name.startswith("علي "):
            name = name[4:]  # « قرأت على مالك »
        link = _make_link(name, cur_term)
        if link is None:
            return
        if coordinated and links:
            link.term, link.mode = links[-1].term, links[-1].mode
            links[-1].alternatives.append(link)
        else:
            links.append(link)

    i = 0
    while i < len(toks):
        tok = toks[i]
        term = _is_term(tok)
        if term:
            flush(final=True)
            cur_term = term
            after_sep = False
        elif tok == "،":
            flush()  # une virgule ne coupe pas une tête de nom incomplète
            after_sep = True
        elif tok in JOIN_WORDS:
            flush(final=True)
            join_at = len(links)
            after_sep = False
        elif tok in FLUSH_WORDS:
            if tok == "و":
                if cur:
                    flush()
                after_sep = True
            else:
                flush(final=True)
                after_sep = tok in {"قالا", "قالوا"} or after_sep
        else:
            if not cur and tok.startswith("و") and len(tok) > 2 and (after_sep or links) and tok[1:].startswith(NAME_STARTS):
                # « ، وأبو كريب » : co-rapporteur du niveau précédent
                cur = [tok[1:]]
                i += 1
                while i < len(toks) and not _is_term(toks[i]) and toks[i] not in JOIN_WORDS and (toks[i] not in FLUSH_WORDS or (toks[i] == "،" and cur[-1] in INCOMPLETE_HEADS)):
                    if toks[i] != "،":
                        cur.append(toks[i])
                    i += 1
                flush(coordinated=True)
                after_sep = False
                continue
            cur.append(tok)
            after_sep = False
        i += 1
    flush(final=True)
    return links, join_at


def chain_summary(chain: Chain) -> str:
    """Représentation lisible « عن عن » : A ← B ← C."""
    parts = []
    for l in chain.links:
        t = f"({l.term}) " if l.term else ""
        alt = (" / " + " / ".join(a.name for a in l.alternatives)) if l.alternatives else ""
        inf = " [inféré]" if l.inferred else ""
        parts.append(f"{t}{l.name}{alt}{inf}")
    return " → ".join(parts)
