"""Mini-évaluation de la recherche : pour des questions à réponse connue, vérifie que le hadith
attendu figure dans le top-k (vecteur seul, lexical seul, hybride)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from hadith_bot import lexical, vector  # noqa: E402
from hadith_bot.db import SessionLocal  # noqa: E402
from hadith_bot.models import Collection, Hadith  # noqa: E402
from hadith_bot.retrieval import hybrid_search  # noqa: E402

# (question, [(recueil, numéro) attendus : au moins un doit apparaître])
GOLD = [
    ("إنما الأعمال بالنيات", [("bukhari", "1"), ("bukhari", "54"), ("muslim", "4927"), ("abudawud", "2201")]),
    ("Actions are judged by intentions", [("bukhari", "1"), ("bukhari", "54"), ("muslim", "4927"), ("abudawud", "2201")]),
    ("fasting on the day of Ashura", [("bukhari", "2000"), ("bukhari", "2001"), ("bukhari", "2002"), ("bukhari", "2003"), ("bukhari", "2004"), ("muslim", "2601"), ("muslim", "2583")]),
    ("صيام يوم عاشوراء", [("bukhari", "2000"), ("bukhari", "2001"), ("bukhari", "2002"), ("bukhari", "2003"), ("bukhari", "2004"), ("muslim", "2601"), ("muslim", "2583"), ("ibnmajah", "1737"), ("ibnmajah", "1738")]),
    ("shortening the prayer while travelling", [("bukhari", "1080"), ("bukhari", "1081"), ("bukhari", "1090"), ("muslim", "1580"), ("muslim", "1581"), ("ibnmajah", "1063")]),
    ("la prière du voyageur, raccourcir la prière en voyage", [("bukhari", "1080"), ("bukhari", "1081"), ("bukhari", "1090"), ("muslim", "1580"), ("muslim", "1581"), ("ibnmajah", "1063"), ("ibnmajah", "1064")]),
    ("صلاة الاستخارة", [("bukhari", "1162"), ("bukhari", "6382"), ("bukhari", "7390"), ("tirmidhi", "480"), ("abudawud", "1538"), ("ibnmajah", "1383")]),
    ("the prayer of istikhara (seeking guidance)", [("bukhari", "1162"), ("bukhari", "6382"), ("bukhari", "7390"), ("tirmidhi", "480"), ("abudawud", "1538"), ("ibnmajah", "1383")]),
    ("الدين النصيحة", [("muslim", "196"), ("abudawud", "4944"), ("nasai", "4197"), ("nasai", "4198"), ("nasai", "4199")]),
    ("Religion is sincerity (nasiha)", [("muslim", "196"), ("abudawud", "4944"), ("nasai", "4197"), ("nasai", "4198"), ("nasai", "4199")]),
    ("les piliers de l'islam : témoignage, prière, zakat, pèlerinage, jeûne de ramadan", [("bukhari", "8"), ("muslim", "16"), ("muslim", "19"), ("muslim", "20"), ("muslim", "21"), ("muslim", "22"), ("tirmidhi", "2609")]),
    ("بني الإسلام على خمس", [("bukhari", "8"), ("muslim", "16"), ("muslim", "19"), ("muslim", "20"), ("muslim", "21"), ("muslim", "22"), ("tirmidhi", "2609")]),
    ("le bon comportement envers les parents, obéissance à la mère", [("bukhari", "5971"), ("muslim", "2548"), ("muslim", "6180"), ("muslim", "6181"), ("muslim", "6182")]),
    ("من كان يؤمن بالله واليوم الآخر فليقل خيرا أو ليصمت", [("bukhari", "6018"), ("bukhari", "6019"), ("bukhari", "6136"), ("bukhari", "6138"), ("bukhari", "6475"), ("muslim", "47"), ("muslim", "75"), ("muslim", "76")]),
]


def main(k: int = 5) -> None:
    with SessionLocal() as s:
        ref = {(slug, num): hid for hid, slug, num in s.execute(select(Hadith.id, Collection.slug, Hadith.hadith_number).join(Collection))}
        scores = {"vector": 0, "lexical": 0, "hybrid": 0}
        for q, expected in GOLD:
            exp_ids = {ref[e] for e in expected if e in ref}
            v = [int(h["hadith_id"]) for h in vector.search([q], k=k)]
            l = [hid for hid, _ in lexical.search(s, q, k=k)]
            h = [d["hadith_id"] for d in hybrid_search(s, [q], k=k)]
            res = {"vector": bool(set(v) & exp_ids), "lexical": bool(set(l) & exp_ids), "hybrid": bool(set(h) & exp_ids)}
            for m, ok in res.items():
                scores[m] += ok
            print(f"{'✓' if res['hybrid'] else '✗'} hybride | vec {'✓' if res['vector'] else '✗'} | lex {'✓' if res['lexical'] else '✗'} | {q}")
        n = len(GOLD)
        print({m: f"{v}/{n}" for m, v in scores.items()})


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
