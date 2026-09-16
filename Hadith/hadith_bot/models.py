"""Schéma relationnel : recueils, hadiths, narrateurs, jugements (Jarh wa Ta'dil), maillons d'isnad."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Collection(Base):
    """Recueil canonique (Bukhari, Muslim, ...)."""

    __tablename__ = "collections"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True)
    name_ar: Mapped[str] = mapped_column(String(128))
    name_fr: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    hadiths: Mapped[list["Hadith"]] = relationship(back_populates="collection")


class Hadith(Base):
    __tablename__ = "hadiths"
    __table_args__ = (
        UniqueConstraint("collection_id", "hadith_number", name="uq_hadith_ref"),
        Index("ix_hadith_collection", "collection_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"))
    hadith_number: Mapped[str] = mapped_column(String(32))  # numérotation du recueil (ex. "1", "2a")
    chapter_number: Mapped[int | None] = mapped_column(Integer)
    chapter_ar: Mapped[str | None] = mapped_column(Text)
    chapter_en: Mapped[str | None] = mapped_column(Text)
    section_number: Mapped[int | None] = mapped_column(Integer)
    section_ar: Mapped[str | None] = mapped_column(Text)
    section_en: Mapped[str | None] = mapped_column(Text)
    text_ar: Mapped[str] = mapped_column(Text)  # hadith complet (isnad + matn)
    isnad_ar: Mapped[str | None] = mapped_column(Text)
    matn_ar: Mapped[str | None] = mapped_column(Text)
    text_en: Mapped[str | None] = mapped_column(Text)
    isnad_en: Mapped[str | None] = mapped_column(Text)
    matn_en: Mapped[str | None] = mapped_column(Text)
    grade_ar: Mapped[str | None] = mapped_column(String(128))  # jugement du recueil / d'al-Albani
    grade_en: Mapped[str | None] = mapped_column(String(128))
    comment_ar: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), default="LK-Hadith-Corpus")

    collection: Mapped[Collection] = relationship(back_populates="hadiths")
    links: Mapped[list["IsnadLink"]] = relationship(
        back_populates="hadith", cascade="all, delete-orphan", order_by="IsnadLink.position"
    )

    @property
    def ref(self) -> str:
        return f"{self.collection.name_fr} n°{self.hadith_number}"


class Narrator(Base):
    """Rapporteur (râwî) avec sa notice biographique et son jugement global."""

    __tablename__ = "narrators"
    __table_args__ = (Index("ix_narrator_norm", "name_norm"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True)  # id source (Itqan / AR-Sanad)
    name_ar: Mapped[str] = mapped_column(Text)  # nom principal
    name_norm: Mapped[str] = mapped_column(Text)  # nom normalisé (sans tashkil) pour la recherche
    name_en: Mapped[str | None] = mapped_column(Text)
    kunya: Mapped[str | None] = mapped_column(Text)
    laqab: Mapped[str | None] = mapped_column(Text)
    nasab: Mapped[str | None] = mapped_column(Text)
    nisba: Mapped[str | None] = mapped_column(Text)
    tabaqa: Mapped[str | None] = mapped_column(String(64))  # génération (Ibn Hajar : 1..12)
    birth_year_h: Mapped[int | None] = mapped_column(Integer)
    death_year_h: Mapped[int | None] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(Text)
    is_companion: Mapped[bool] = mapped_column(default=False)
    # Jugements globaux (texte source) + catégorie/rang calculés
    grade_ibn_hajar: Mapped[str | None] = mapped_column(Text)  # Taqrîb al-Tahdhîb
    grade_dhahabi: Mapped[str | None] = mapped_column(Text)  # al-Kâshif / Mîzân
    grade_category: Mapped[str] = mapped_column(String(32), default="unknown")
    # companion | thiqa | saduq | maqbul | daif | matruk | kadhdhab | unknown
    grade_rank: Mapped[int | None] = mapped_column(Integer)  # 6 (compagnon) ... 0 (menteur) ; NULL = inconnu
    sources: Mapped[dict | list | None] = mapped_column(JSON)  # citations des ouvrages classiques
    extra: Mapped[dict | None] = mapped_column(JSON)

    names: Mapped[list["NarratorName"]] = relationship(back_populates="narrator", cascade="all, delete-orphan")
    opinions: Mapped[list["NarratorOpinion"]] = relationship(
        back_populates="narrator", cascade="all, delete-orphan"
    )


class NarratorName(Base):
    """Variantes de noms (kunya, nisba, formes abrégées) utilisées pour l'appariement."""

    __tablename__ = "narrator_names"
    __table_args__ = (Index("ix_narrator_name_norm", "name_norm"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    narrator_id: Mapped[int] = mapped_column(ForeignKey("narrators.id", ondelete="CASCADE"))
    name_ar: Mapped[str] = mapped_column(Text)
    name_norm: Mapped[str] = mapped_column(Text)
    narrator: Mapped[Narrator] = relationship(back_populates="names")


class NarratorOpinion(Base):
    """Avis d'un critique (jarh ou ta'dil) sur un narrateur, avec sa source."""

    __tablename__ = "narrator_opinions"
    id: Mapped[int] = mapped_column(primary_key=True)
    narrator_id: Mapped[int] = mapped_column(ForeignKey("narrators.id", ondelete="CASCADE"))
    critic: Mapped[str | None] = mapped_column(Text)  # ex. أحمد بن حنبل، أبو حاتم، ابن معين
    opinion: Mapped[str] = mapped_column(Text)  # ex. ثقة ثبت / ضعيف الحديث
    kind: Mapped[str | None] = mapped_column(String(16))  # tadil | jarh | mixed | unknown
    source_book: Mapped[str | None] = mapped_column(Text)  # ex. الجرح والتعديل، تهذيب الكمال
    narrator: Mapped[Narrator] = relationship(back_populates="opinions")


class IsnadLink(Base):
    """Un maillon de la chaîne d'un hadith : nom tel qu'écrit, terme de transmission, narrateur lié."""

    __tablename__ = "isnad_links"
    __table_args__ = (Index("ix_link_hadith", "hadith_id"), Index("ix_link_narrator", "narrator_id"))
    id: Mapped[int] = mapped_column(primary_key=True)
    hadith_id: Mapped[int] = mapped_column(ForeignKey("hadiths.id", ondelete="CASCADE"))
    chain_no: Mapped[int] = mapped_column(Integer, default=0)  # plusieurs chaînes si تحويل (ح)
    position: Mapped[int] = mapped_column(Integer)  # 0 = maître du compilateur ... n = compagnon
    name_as_written: Mapped[str] = mapped_column(Text)
    name_norm: Mapped[str] = mapped_column(Text)
    transmission_term: Mapped[str | None] = mapped_column(String(32))  # حدثنا / أخبرنا / عن / سمعت ...
    transmission_mode: Mapped[str | None] = mapped_column(String(16))  # sama | anana | other
    is_relative: Mapped[bool] = mapped_column(default=False)  # "عن أبيه", "عن جده" ...
    narrator_id: Mapped[int | None] = mapped_column(ForeignKey("narrators.id", ondelete="SET NULL"))
    match_score: Mapped[float | None] = mapped_column(Float)
    match_method: Mapped[str | None] = mapped_column(String(16))  # exact | fuzzy | none

    hadith: Mapped[Hadith] = relationship(back_populates="links")
    narrator: Mapped[Narrator | None] = relationship()


class QueryLog(Base):
    """Journal des requêtes (audit / amélioration)."""

    __tablename__ = "query_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    question: Mapped[str] = mapped_column(Text)
    hadith_ids: Mapped[list | None] = mapped_column(JSON)
    llm_used: Mapped[bool] = mapped_column(default=False)
