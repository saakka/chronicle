"""Appariement des noms d'isnad aux notices de narrateurs (exact -> flou -> désambiguïsation par
les relations maître/élève, résolution des références relatives « أبيه / جده »)."""
from __future__ import annotations

from dataclasses import dataclass, field

from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.orm import Session

from .arabic import normalize_name
from .config import settings
from .models import Narrator, NarratorName


@dataclass
class NarratorInfo:
    id: int
    ext: int | None  # id Itqan (espace des listes teachers/students)
    exts: set[int]  # id principal + ids des doublons fusionnés
    name: str
    name_norm: str
    kunya_norm: str
    rank: int | None
    confidence: str | None
    teachers: set[int]
    students: set[int]
    death: int | None


@dataclass
class Match:
    narrator_id: int | None
    score: float
    method: str  # exact | exact+ctx | fuzzy | fuzzy+ctx | relative | ambiguous | none
    candidates: list[int] = field(default_factory=list)


class NarratorIndex:
    """Index en mémoire (≈115k narrateurs, ≈330k variantes de noms)."""

    def __init__(self, session: Session):
        self.by_name: dict[str, list[int]] = {}
        for nn, nid in session.execute(select(NarratorName.name_norm, NarratorName.narrator_id)):
            self.by_name.setdefault(nn, []).append(nid)
        self.info: dict[int, NarratorInfo] = {}
        self.by_ext: dict[int, int] = {}
        rows = session.execute(
            select(Narrator.id, Narrator.external_id, Narrator.name_ar, Narrator.kunya, Narrator.grade_rank, Narrator.death_year_h, Narrator.extra)
        )

        def _num(e: str | None) -> int | None:
            return int(e.split(":")[1]) if e and e.startswith("itqan:") and e.split(":")[1].isdigit() else None

        for nid, ext, name, kunya, rank, death, extra in rows:
            extra = extra or {}
            ext_i = _num(ext)
            exts = {x for x in [ext_i, *(_num(a) for a in extra.get("merged_ids") or [])] if x is not None}
            self.info[nid] = NarratorInfo(
                id=nid, ext=ext_i, exts=exts, name=name, name_norm=normalize_name(name), kunya_norm=normalize_name((kunya or "").split("،")[0]),
                rank=rank, confidence=extra.get("confidence"),
                teachers=set(extra.get("teachers") or []), students=set(extra.get("students") or []), death=death,
            )
            for x in exts:
                self.by_ext[x] = nid
        for nid in self.info:
            self.by_name.setdefault(self.info[nid].name and normalize_name(self.info[nid].name), []).append(nid)
        # seaux par premier jeton (ou deux premiers pour أبو/ابن/عبد...) : le flou reste rapide
        self._buckets: dict[str, list[str]] = {}
        for nn in self.by_name:
            self._buckets.setdefault(self._bucket_key(nn), []).append(nn)
        self._fuzzy_cache: dict[str, tuple[str | None, float]] = {}

    _GENERIC = {"ابو", "ابن", "ابي", "ام", "عبد", "بن", "ال"}

    @classmethod
    def _bucket_key(cls, nn: str) -> str:
        t = nn.split()
        if not t:
            return ""
        return " ".join(t[:2]) if t[0] in cls._GENERIC and len(t) > 1 else t[0]

    # ---- candidats -------------------------------------------------------------------------
    def candidates(self, name_norm: str) -> tuple[list[int], float, str]:
        # « أبي هريرة » (génitif dans l'isnad) et « أبو هريرة » (nominatif dans les notices) : même personne
        forms = [name_norm, *self._kunya_forms(name_norm)]
        ids: set[int] = set()
        for f in forms:
            ids.update(self.by_name.get(f) or [])
        if ids:
            return sorted(ids), 100.0, "exact"
        for variant in self._variants(name_norm):
            ids.update(self.by_name.get(variant) or [])
            if ids:
                return sorted(ids), 96.0, "exact"
        best = self._fuzzy(name_norm)
        if best[0] is not None:
            return sorted(set(self.by_name[best[0]])), best[1], "fuzzy"
        return [], 0.0, "none"

    @staticmethod
    def _kunya_forms(nn: str) -> list[str]:
        t = nn.split()
        if not t:
            return []
        out = []
        for i, w in enumerate(t):
            if w in ("ابو", "ابي") and (i == 0 or t[i - 1] == "بن"):
                for alt in ("ابو", "ابي"):
                    if alt != w:
                        out.append(" ".join([*t[:i], alt, *t[i + 1 :]]))
        return out

    @staticmethod
    def _variants(nn: str) -> list[str]:
        """Formes équivalentes : accusatif « أنسا », nisba finale en trop."""
        t = nn.split()
        out: list[str] = []
        if t and t[-1].endswith("ا") and len(t[-1]) > 3 and t[-1] not in ("زكريا", "عطا", "عبدالاعلي"):
            out.append(" ".join([*t[:-1], t[-1][:-1]]))
        if len(t) >= 4 and t[-2] != "بن" and t[-1].startswith("ال"):
            out.append(" ".join(t[:-1]))  # « عبد الله بن يوسف التنيسي » -> sans nisba
        return out

    def _fuzzy(self, q: str) -> tuple[str | None, float]:
        if q in self._fuzzy_cache:
            return self._fuzzy_cache[q]
        bucket = self._buckets.get(self._bucket_key(q)) or []
        res = process.extractOne(q, bucket, scorer=fuzz.token_sort_ratio, score_cutoff=settings.fuzzy_threshold) if bucket else None
        out = (res[0], float(res[1])) if res else (None, 0.0)
        self._fuzzy_cache[q] = out
        return out

    # ---- désambiguïsation par contexte -------------------------------------------------------
    def _ctx_score(self, nid: int, prev_ids: set[int], next_ids: set[int], *, last: bool = False, name_norm: str = "") -> float:
        i = self.info[nid]
        sc = 0.0
        prev_ext: set[int] = set()
        for p in prev_ids:
            if p in self.info:
                prev_ext |= self.info[p].exts
        next_ext: set[int] = set()
        for n in next_ids:
            if n in self.info:
                next_ext |= self.info[n].exts
        t = name_norm.split()
        if len(t) == 2 and t[0] == "بن":  # « ابن عمر » : le père du candidat doit s'appeler عمر
            ct = i.name_norm.split()
            sc += 3 if len(ct) >= 3 and ct[1] == "بن" and ct[2] == t[1] else -2
        elif len(t) == 2 and t[0] in ("ابو", "ابي") and i.kunya_norm:  # « أبو معاوية » : kunya du candidat
            sc += 2 if i.kunya_norm.replace("ابي", "ابو") == name_norm.replace("ابي", "ابو") else 0
        if prev_ext & i.students:  # le maillon précédent (élève) a bien appris de lui
            sc += 4
        if next_ext & i.teachers:  # le maillon suivant est bien son maître
            sc += 4
        if i.rank is not None:
            sc += 0.5
        sc += {"A": 0.6, "B": 0.4, "C": 0.2}.get(i.confidence or "", 0)
        sc += min(len(i.teachers) + len(i.students), 400) / 200  # notoriété (max 2) : écarte les doublons vides
        if i.rank == 6:  # Compagnon : attendu en fin de chaîne, rare au milieu (il ne rapporte pas d'un tâbi'î)
            sc += 3 if last else -2.5
        return sc

    def link_chain(self, links: list[dict]) -> list[Match]:
        """`links` : dicts {name_norm, is_relative, alternatives:[{name_norm}...]} ordonnés élève -> maître."""
        cands: list[tuple[list[int], float, str]] = []
        for l in links:
            if l.get("is_relative"):
                cands.append(([], 0.0, "relative"))
            else:
                cands.append(self.candidates(l["name_norm"]))
        chosen: list[Match] = [Match(None, 0.0, "none") for _ in links]
        # deux passes : les voisins déjà choisis affinent les ambigus
        for _ in range(2):
            for i, (ids, score, method) in enumerate(cands):
                if method == "relative":
                    continue
                if not ids:
                    chosen[i] = Match(None, 0.0, "none")
                    continue
                prev_ids = set(chosen[i - 1].candidates or ([chosen[i - 1].narrator_id] if chosen[i - 1].narrator_id else [])) if i > 0 else set()
                next_ids = set(cands[i + 1][0]) if i + 1 < len(cands) else set()
                if len(ids) == 1:
                    chosen[i] = Match(ids[0], score, method, ids)
                    continue
                last = i == len(cands) - 1
                scored = sorted(((self._ctx_score(n, prev_ids, next_ids, last=last, name_norm=links[i]["name_norm"]), n) for n in ids), reverse=True)
                top, second = scored[0], scored[1] if len(scored) > 1 else (0, None)
                gap = top[0] - second[0]
                if gap >= 2.5:
                    chosen[i] = Match(top[1], min(score, 97.0), method + "+ctx", ids)
                elif gap >= 0.75:
                    chosen[i] = Match(top[1], min(score, 75.0), "ambiguous", ids)
                else:
                    chosen[i] = Match(top[1], min(score, 55.0), "ambiguous", ids)
        # références relatives : « عن أبيه » = père du maillon précédent
        for i, l in enumerate(links):
            if not l.get("is_relative") or i == 0:
                continue
            prev = chosen[i - 1].narrator_id
            if prev is None:
                continue
            head = l["name_norm"].split()[0]
            chosen[i] = self._resolve_relative(head, prev)
        return chosen

    def _resolve_relative(self, head: str, prev_id: int) -> Match:
        name = normalize_name(self.info[prev_id].name)
        parts = name.split()
        depth = {"ابيه": 1, "ابي": 1, "ابيها": 1, "جده": 2, "جدها": 2, "جدي": 2}.get(head)
        if not depth:
            return Match(None, 0.0, "none")
        # « هشام بن عروه بن الزبير » -> père = « عروه بن الزبير », grand-père = « الزبير ... »
        idx = [k for k, w in enumerate(parts) if w == "بن"]
        if len(idx) < depth:
            return Match(None, 0.0, "none")
        tail = parts[idx[depth - 1] + 1 :]
        ids: list[int] = []
        # « عروه بن الزبير بن العوام » -> essais du plus long au plus court (jusqu'à « عروه بن الزبير »)
        for n in range(len(tail), 2, -1):
            ids = self.by_name.get(" ".join(tail[:n])) or []
            if ids:
                break
        if not ids and len(tail) == 1:
            ids = self.by_name.get(tail[0]) or []
        if not ids:
            return Match(None, 0.0, "none")
        prev_exts = self.info[prev_id].exts
        best = sorted(set(ids), key=lambda n: (bool(prev_exts & self.info[n].students), len(self.info[n].students) + len(self.info[n].teachers), self.info[n].rank is not None), reverse=True)
        top = best[0]
        conf = 90.0 if prev_exts & self.info[top].students else (70.0 if len(set(ids)) == 1 else 50.0)
        return Match(top, conf, "relative", sorted(set(ids)))
