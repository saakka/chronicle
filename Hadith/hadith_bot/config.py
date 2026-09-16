"""Configuration centrale (variables d'environnement / fichier .env)."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_prefix="HADITH_", extra="ignore")

    # Base relationnelle : PostgreSQL en production, SQLite en local par défaut.
    #   ex. postgresql+psycopg://user:pass@localhost:5432/hadith
    database_url: str = f"sqlite:///{DATA_DIR / 'hadith.sqlite3'}"

    # Base vectorielle (ChromaDB persistant) et modèle d'embedding multilingue (ar/fr/en).
    chroma_dir: Path = DATA_DIR / "chroma"
    chroma_collection: str = "hadiths_v2"
    embedding_model: str = "intfloat/multilingual-e5-small"

    # Dossier des données brutes téléchargées (corpus LK, base Itqan).
    raw_dir: Path = DATA_DIR / "raw"

    # Modèle de langage : "local" (MLX, Qwen 2.5 7B sur Apple Silicon, aucune API), "anthropic" (Claude, clé requise)
    # ou "none". Le modèle comprend la question, juge la pertinence, extrait les réponses et rédige ; il ne note jamais.
    llm_backend: str = "local"
    local_model: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    llm_enabled: bool = True
    llm_model: str = "claude-opus-5"
    llm_max_tokens: int = 4000

    # Recherche
    top_k: int = 15
    fuzzy_threshold: int = 88  # score rapidfuzz minimal pour lier un nom d'isnad à un narrateur


settings = Settings()
