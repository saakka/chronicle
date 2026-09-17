"""Normalisation de l'arabe pour l'appariement de noms et la recherche."""
from __future__ import annotations

import re

_TASHKIL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ‏‎‪-‮]")
_ALEF = re.compile(r"[إأآٱ]")
_HONORIFICS = [
    r"صلى الله عليه وسلم",
    r"صلى الله عليه و سلم",
    r"عليه السلام",
    r"عليه الصلاة والسلام",
    r"رضي الله عنهم?ا?",
    r"رضى الله عنهم?ا?",
    r"رضي الله عنها",
    r"رحمه الله",
    r"رحمها الله",
    r"تعالى",
]
_HONORIFIC_RE = re.compile("|".join(_HONORIFICS))
_PUNCT = re.compile(r"[،؛؟\.,;:!\?\"'«»\(\)\[\]\{\}\-–—ـ]+")
_WS = re.compile(r"\s+")


def strip_tashkil(s: str) -> str:
    return _TASHKIL.sub("", s)


def normalize(s: str | None, *, keep_spaces: bool = True) -> str:
    """Forme canonique : sans voyelles, alef unifié, ة→ه, ى→ي, honorifiques et ponctuation retirés."""
    if not s:
        return ""
    s = strip_tashkil(s)
    s = _HONORIFIC_RE.sub(" ", s)
    s = _ALEF.sub("ا", s)
    s = s.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    s = s.replace("الرحمان", "الرحمن")  # graphie « عبد الرحمان » des textes imamites
    s = _PUNCT.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s if keep_spaces else s.replace(" ", "")


def normalize_name(s: str | None) -> str:
    """Normalisation de nom : en plus, unifie ابن/بن et retire les articles isolés."""
    s = normalize(s)
    s = re.sub(r"\b(هو|وهو|يعني|اعني|هي|وهي)\b", " ", s)  # « يحيى هو ابن سعيد » -> « يحيى بن سعيد »
    s = re.sub(r"\bابن\b", "بن", s)
    s = re.sub(r"\bابا\b", "ابي", s)  # accusatif « سمعت أبا هريرة »
    s = re.sub(r"\bعبد الله\b", "عبدالله", s)
    s = re.sub(r"\bعبد الرحمن\b", "عبدالرحمن", s)
    s = re.sub(r"\bعبيد الله\b", "عبيدالله", s)
    s = re.sub(r"\bعبد الملك\b", "عبدالملك", s)
    s = re.sub(r"\bعبد العزيز\b", "عبدالعزيز", s)
    s = re.sub(r"\bعبد الوهاب\b", "عبدالوهاب", s)
    s = re.sub(r"\bعبد الرزاق\b", "عبدالرزاق", s)
    s = re.sub(r"\bعبد الواحد\b", "عبدالواحد", s)
    s = re.sub(r"\bعبد الكريم\b", "عبدالكريم", s)
    s = re.sub(r"\bعبد الصمد\b", "عبدالصمد", s)
    return _WS.sub(" ", s).strip()
