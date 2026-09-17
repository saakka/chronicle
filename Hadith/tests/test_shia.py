from hadith_bot.grading_shia import classify_majlisi, classify_shia, grade_chain_shia, score_hadith_shia
from hadith_bot.isnad_shia import parse_isnad_shia


def names(chain):
    return [(l.name_norm, l.kind) for l in chain.links]


def test_parse_kafi_chain_ends_with_imam():
    chains, matn = parse_isnad_shia("12 علي بن إبراهيم عن أبيه عن ابن أبي عمير عن الحكم بن مسكين عن أبي عبد الله (عليه السلام) قال من أدخل على مؤمن سرورا")
    assert names(chains[0]) == [("علي بن ابراهيم", "normal"), ("ابيه", "relative"), ("بن ابي عمير", "normal"), ("الحكم بن مسكين", "normal"), ("ابي عبدالله", "imam")]
    assert matn.startswith("قال من ادخل")


def test_parse_idda_and_marfu():
    chains, _ = parse_isnad_shia("عدة من أصحابنا عن سهل بن زياد عن يحيى بن المبارك رفعه قال قال رسول الله (صلى الله عليه وآله) كذا")
    kinds = [l.kind for l in chains[0].links]
    assert kinds[0] == "group" and "marfu" in kinds and kinds[-1] == "imam"


def test_parse_previous_chain_reference():
    prev, _ = parse_isnad_shia("1 محمد بن يحيى عن أحمد بن محمد عن ابن فضال عن أبي جعفر (عليه السلام) قال كذا")
    chains, _ = parse_isnad_shia("2 وعنه عن أحمد بن محمد عن الحسن بن الجهم قال قلت لأبي الحسن (عليه السلام) كذا", prev[0].links)
    assert names(chains[0])[0] == ("محمد بن يحيي", "normal")
    assert names(chains[0])[-1] == ("ابي الحسن", "imam")


def test_classify_shia():
    assert classify_shia("السجستاني - ثقة - من أصحاب الصادق") == ("thiqa", 5)
    assert classify_shia("واقفي - ثقة") == ("muwaththaq", 4)
    assert classify_shia("من أصحاب الصادق (ع) - مجهول") == ("majhul", None)
    assert classify_shia("ثقة - له كتاب - طريق الصدوق إليه ضعيف") == ("thiqa", 5)
    assert classify_shia("لا ينبغي الشك في وثاقته") == ("thiqa", 5)
    assert classify_shia("ضعيف غال") == ("kadhdhab", 0)


def L(name, cat=None, kind="normal", method="exact"):
    nar = {"grade_category": cat, "name": name} if cat else None
    return {"name": name, "kind": kind, "match_method": method, "narrator": nar, "alternatives": []}


def test_chain_verdicts():
    assert grade_chain_shia([L("a", "thiqa"), L("b", "thiqa"), L("imam", "imam", kind="imam")])["code"] == "sahih"
    assert grade_chain_shia([L("a", "thiqa"), L("b", "muwaththaq"), L("imam", "imam", kind="imam")])["code"] == "muwaththaq"
    assert grade_chain_shia([L("a", "mamduh"), L("b", "thiqa")])["code"] == "hasan"
    assert grade_chain_shia([L("a", "thiqa"), L("b", "majhul")])["code"] == "daif_majhul"
    assert grade_chain_shia([L("a", "thiqa"), L("x", None)])["code"] == "daif_majhul"
    assert grade_chain_shia([L("a", "thiqa"), L("r", None, kind="marfu")])["code"] == "daif_mursal"
    assert grade_chain_shia([L("a", "kadhdhab")])["code"] == "daif_jiddan"
    assert grade_chain_shia([L("g", "group", kind="group"), L("b", "thiqa")])["code"] == "sahih"


def test_majlisi_scale():
    assert classify_majlisi("صحيح") == 4 and classify_majlisi("موثق ول يقصر عن الصحيح") == 4 and classify_majlisi("حسن كالصحيح") == 4
    assert classify_majlisi("حسن") == 3 and classify_majlisi("ضعيف على المشهور") == 2 and classify_majlisi("مجهول") == 2 and classify_majlisi("مرسل") == 2
    assert classify_majlisi("مختلف فيه") is None
    ch = [{"verdict": {"code": "sahih"}}]
    assert score_hadith_shia("صحيح", ch)["score"] == 4  # le 5 vient de la corroboration
    assert score_hadith_shia("ضعيف", ch)["score"] == 2
    assert score_hadith_shia(None, [{"verdict": {"code": "hasan"}}])["score"] == 3
