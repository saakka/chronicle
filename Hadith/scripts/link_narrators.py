"""Relie chaque maillon d'isnad à une notice de narrateur (appariement + désambiguïsation)."""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update  # noqa: E402

from hadith_bot.db import SessionLocal  # noqa: E402
from hadith_bot.matching import NarratorIndex  # noqa: E402
from hadith_bot.models import Collection, Hadith, IsnadLink  # noqa: E402


def main(slugs: list[str] | None = None, tradition: str | None = None) -> None:
    with SessionLocal() as s:
        traditions = [tradition] if tradition else [t for (t,) in s.execute(select(Collection.tradition).distinct())]
        for trad in traditions:
            print(f"[{trad}] chargement de l'index des narrateurs…")
            index = NarratorIndex(s, tradition=trad)
            print(f"  {len(index.info)} narrateurs, {len(index.by_name)} noms")
            _link_tradition(s, index, trad, slugs)


def _link_tradition(s, index: NarratorIndex, trad: str, slugs: list[str] | None) -> None:
    if True:
        q = (select(IsnadLink.id, IsnadLink.hadith_id, IsnadLink.chain_no, IsnadLink.position, IsnadLink.name_norm, IsnadLink.is_relative, IsnadLink.kind)
             .join(Hadith).join(Collection).where(Collection.tradition == trad))
        if slugs:
            q = q.where(Collection.slug.in_(slugs))
        chains: dict[tuple[int, int], dict[int, list[tuple[int, str, bool, str]]]] = defaultdict(lambda: defaultdict(list))
        for lid, hid, cno, pos, nn, rel, kind in s.execute(q):
            chains[(hid, cno)][pos].append((lid, nn, rel, kind or "normal"))
        print(f"  {len(chains)} chaînes à lier")
        stats = defaultdict(int)
        updates = []
        for n, ((hid, cno), positions) in enumerate(chains.items()):
            ordered = [positions[p] for p in sorted(positions)]
            main_links = [{"name_norm": alts[0][1], "is_relative": alts[0][2], "kind": alts[0][3]} for alts in ordered]
            matches = index.link_chain(main_links)
            for alts, m in zip(ordered, matches):
                updates.append({"id": alts[0][0], "narrator_id": m.narrator_id, "match_score": m.score, "match_method": m.method})
                stats[m.method] += 1
                for lid, nn, rel, kind in alts[1:]:
                    ids, score, method = ([], 0.0, "none") if (rel or kind in ("unnamed", "marfu")) else index.candidates(nn)
                    nid = ids[0] if len(ids) == 1 else (ids[0] if ids else None)
                    meth = method if len(ids) == 1 else ("ambiguous" if ids else "none")
                    updates.append({"id": lid, "narrator_id": nid, "match_score": score if nid else 0.0, "match_method": meth})
                    stats[meth] += 1
            if len(updates) >= 5000:
                s.execute(update(IsnadLink), updates)
                s.commit()
                updates = []
            if n % 5000 == 0 and n:
                print(f"  {n} chaînes…", dict(stats))
        if updates:
            s.execute(update(IsnadLink), updates)
            s.commit()
        print("terminé :", dict(stats))


if __name__ == "__main__":
    args = sys.argv[1:]
    trad = None
    if args and args[0] in ("sunni", "shia"):
        trad = args.pop(0)
    main(args or None, trad)
