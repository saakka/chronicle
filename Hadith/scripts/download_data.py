"""Télécharge les données brutes : corpus LK (6 recueils, isnad/matn séparés) et base narrateurs Itqan."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from urllib.request import urlretrieve

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from hadith_bot.config import settings  # noqa: E402

RAW = settings.raw_dir
LK_REPO = "https://github.com/ShathaTm/LK-Hadith-Corpus.git"
ITQAN_RAW = "https://raw.githubusercontent.com/R3GENESI5/Itqan/master/"
ITQAN_FILES = [
    "app/data/rijal/manifest.json",
    "app/data/rijal/profiles_companion.json",
    "app/data/rijal/profiles_reliable.json",
    "app/data/rijal/profiles_mostly_reliable.json",
    "app/data/rijal/profiles_weak.json",
    "app/data/rijal/profiles_abandoned.json",
    "app/data/rijal/profiles_fabricator.json",
    "app/data/rijal/profiles_unknown.json",
    "src/external_narrators_db.json",
    "src/arsanad_narrators.csv",
]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    lk = RAW / "LK-Hadith-Corpus"
    if not lk.exists():
        print("clone", LK_REPO)
        subprocess.run(["git", "clone", "--depth", "1", LK_REPO, str(lk)], check=True)
    else:
        print("ok", lk)
    itqan = RAW / "itqan"
    for rel in ITQAN_FILES:
        dest = itqan / rel
        if dest.exists():
            print("ok", dest.relative_to(RAW))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        print("get", rel)
        urlretrieve(ITQAN_RAW + rel, dest)
    print("done ->", RAW)


if __name__ == "__main__":
    main()
