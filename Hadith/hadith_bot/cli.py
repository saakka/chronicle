"""Usage : python -m hadith_bot.cli "question" [--no-llm] [-k 5] [--json]"""
from __future__ import annotations

import argparse
import json

from .db import SessionLocal, init_db
from .retrieval import ask, format_synthesis


def main() -> None:
    p = argparse.ArgumentParser(description="Bot Hadiths & 'Ilm al-Rijal")
    p.add_argument("question")
    p.add_argument("-k", type=int, default=None)
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    init_db()
    with SessionLocal() as s:
        out = ask(s, a.question, k=a.k, use_llm=not a.no_llm)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if out.get("synthesis"):
            print(format_synthesis(out["synthesis"]))
            print()
        print(out["answer"])
        print(f"\n[LLM utilisé : {out['llm_used']} | requêtes : {out['queries']}]")


if __name__ == "__main__":
    main()
