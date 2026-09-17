from hadith_bot.local_llm import _extract_json, group
from hadith_bot import local_llm


def test_extract_json_variants():
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert _extract_json('Voici : [{"id": 1}] fin') == [{"id": 1}]
    assert _extract_json("rien") is None


def test_group_by_numbers():
    claims = [{"id": 1, "answer": "6 ans", "answer_key": "6"}, {"id": 2, "answer": "six ans", "answer_key": "6"}, {"id": 3, "answer": "7 ans", "answer_key": "7"}]
    assert [x["ids"] for x in group("q", claims)] == [[1, 2], [3]]


def test_group_arabic_numbers_distinct():
    claims = [
        {"id": 1, "answer": "تزوجها وهي بنت ست، وبنى بها وهي بنت تسع", "answer_key": "6 / 9"},
        {"id": 2, "answer": "تزوجها وهي بنت سبع وبنى بها وهي بنت تسع وتوفي عنها وهي بنت ثمان عشرة", "answer_key": "7 / 9"},
        {"id": 3, "answer": "تزوجها وهي بنت ست وبنى بها وهي بنت تسع ومات عنها وهي بنت ثمان عشرة", "answer_key": "6 / 9 / 18"},
    ]
    g = group("q", claims)
    assert [x["ids"] for x in g] == [[1, 3], [2]]  # 6/9 (avec ou sans le détail 18) vs 7/9
    from hadith_bot.local_llm import _num_signature
    assert _num_signature(claims[1]["answer"]) == "7 9 18"
    assert _num_signature("six ans puis neuf") == "6 9"
    assert _num_signature("تزوجني رسول الله لسبعة ودخل علي لتسعة") == "7 9"


def test_salvage_truncated_list():
    assert _extract_json('[{"id": 1, "answer": "a"}, {"id": 2, "answer": "tron') == [{"id": 1, "answer": "a"}]


def test_verify_claim_against_text():
    from hadith_bot.local_llm import verify_claim
    c = verify_claim({"id": 1, "answer": "تزوجها وهي بنت سبع وبنى بها وهي بنت تسع"}, "تزوجها رسول الله وهي بنت ست وبنى بها وهي بنت تسع")
    assert c["verified"] is False and c["sig"] == "6 9"  # reclassé d'après le texte
    c = verify_claim({"id": 2, "answer": "تزوجها وهي بنت ست وبنى بها وهي بنت تسع"}, "تزوجها وهي بنت ست وبنى بها وهي بنت تسع ومات عنها وهي بنت ثمان عشرة")
    assert c["verified"] is True and c["sig"] == "6 9"


def test_partial_claim_regrouped_by_text():
    from hadith_bot.local_llm import verify_claim
    c = verify_claim({"id": 3, "answer": "وهي بنت تسع ومات عنها وهي بنت ثمان عشرة"}, "تزوجها وهي بنت ست وبنى بها وهي بنت تسع ومات عنها وهي بنت ثمان عشرة")
    assert c["verified"] is True and c["sig"] == "6 9"
