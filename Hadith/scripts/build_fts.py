"""Construit l'index lexical (FTS5 / tsvector) des hadiths."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hadith_bot.db import SessionLocal  # noqa: E402
from hadith_bot import lexical  # noqa: E402

if __name__ == "__main__":
    with SessionLocal() as s:
        n = lexical.build(s)
    print(f"index lexical : {n} hadiths")
