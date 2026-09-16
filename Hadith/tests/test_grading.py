from hadith_bot.grading import classify_grade_text, grade_chain


def test_classify():
    assert classify_grade_text("ثقة ثبت") == ("thiqa", 5)
    assert classify_grade_text("صدوق يخطئ") == ("maqbul", 3)
    assert classify_grade_text("لا بأس به") == ("saduq", 4)
    assert classify_grade_text("ضعيف") == ("daif", 2)
    assert classify_grade_text("متروك الحديث") == ("matruk", 1)
    assert classify_grade_text("كذاب") == ("kadhdhab", 0)
    assert classify_grade_text("له صحبة") == ("companion", 6)
    assert classify_grade_text("استنباط من الأسانيد (3 إسناد)") == (None, None)
    assert classify_grade_text("") == (None, None)


def L(name, rank=None, resolved=True, mode="sama", alts=()):
    nar = {"grade_rank": rank} if resolved else None
    return {"name": name, "mode": mode, "narrator": nar, "alternatives": [{"name": a[0], "narrator": {"grade_rank": a[1]}} for a in alts]}


def test_chain_sahih():
    v = grade_chain([L("a", 5), L("b", 5), L("c", 6)])
    assert v.code == "sahih_rijal" and v.weakest in ("a", "b")


def test_chain_weakest_link():
    assert grade_chain([L("a", 5), L("b", 2), L("c", 6)]).code == "daif"
    assert grade_chain([L("a", 5), L("b", 1)]).code == "daif_jiddan"
    assert grade_chain([L("a", 4), L("b", 5)]).code == "hasan_rijal"
    assert grade_chain([L("a", 3), L("b", 5)]).code == "hasan_in_tubia"


def test_chain_incomplete_and_alternatives():
    v = grade_chain([L("a", 5), L("b", resolved=False), L("c", 6)])
    assert v.code == "incomplete" and v.unresolved == ["b"]
    # un co-rapporteur fiable suffit au niveau concerné
    assert grade_chain([L("a", 2, alts=[("a2", 5)]), L("b", 5)]).code == "sahih_rijal"


from hadith_bot.grading import classify_source_grade, score_hadith, score_topic


def _chain(code, weakest="x", method="exact"):
    return {"links": [{"name": weakest, "match_method": method}], "verdict": {"code": code, "weakest": weakest, "label_ar": code}}


def test_source_grade():
    assert classify_source_grade("صحيح")[0] == 4
    assert classify_source_grade("حسن صحيح")[0] == 4
    assert classify_source_grade("حسن")[0] == 3
    assert classify_source_grade("ضعيف")[0] == 2
    assert classify_source_grade("منكر")[0] == 1
    assert classify_source_grade("صحيح موقوف")[1]
    assert classify_source_grade(None) == (None, [])


def test_score_hadith():
    assert score_hadith("bukhari", "صحيح", [_chain("sahih_rijal")])["score"] == 5
    assert score_hadith("bukhari", "صحيح", [_chain("incomplete")])["score"] == 4
    assert score_hadith("tirmidhi", "صحيح", [_chain("sahih_rijal")])["score"] == 4
    assert score_hadith("tirmidhi", "حسن", [_chain("hasan_rijal")])["score"] == 3
    assert score_hadith("tirmidhi", "ضعيف", [_chain("daif")])["score"] == 2
    assert score_hadith("abudawud", "منكر", [_chain("daif_jiddan")])["score"] == 1
    # divergence : recueil صحيح mais narrateur faible identifié avec certitude -> -1 ; ambigu -> inchangé
    assert score_hadith("ibnmajah", "صحيح", [_chain("daif", method="exact")])["score"] == 3
    assert score_hadith("ibnmajah", "صحيح", [_chain("daif", method="ambiguous")])["score"] == 4
    assert score_hadith("nasai", None, [_chain("sahih_rijal")])["score"] == 4
    assert score_hadith("nasai", None, [_chain("incomplete")])["score"] is None


def _res(i, coll, score, rel, comp="c"):
    return {"id": i, "collection": coll, "reference": f"{coll} n°{i}", "score": score, "reliability": {"score": rel, "reasons": ["r"]},
            "chains": [{"links": [{"name": comp, "name_norm": comp}], "verdict": {"code": "sahih_rijal"}}]}


def test_score_topic():
    assert score_topic([])["score"] == 0
    assert score_topic([_res(1, "bukhari", 0.03, 5)])["score"] == 5
    # deux rapports صحيح de recueils différents -> 5 (corroboration)
    assert score_topic([_res(1, "tirmidhi", 0.03, 4, "a"), _res(2, "abudawud", 0.028, 4, "b")])["score"] == 5
    # un seul rapport صحيح dans un Sunan -> 4
    assert score_topic([_res(1, "tirmidhi", 0.03, 4), _res(2, "abudawud", 0.028, 2)])["score"] == 4
    # sélection explicite par le LLM
    assert score_topic([_res(1, "bukhari", 0.03, 5), _res(2, "tirmidhi", 0.02, 2)], relevant_ids=[2])["score"] == 2
