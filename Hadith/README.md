# Bot Hadiths & ʿIlm al-Rijāl

Assistant conversationnel qui, pour une question thématique en langage naturel (français, anglais ou arabe) :

1. retrouve les hadiths pertinents dans **les six recueils canoniques** (recherche sémantique / RAG) ;
2. extrait la **chaîne de transmission** (isnad : حدثنا … عن … عن …) ;
3. interroge une **base relationnelle des narrateurs** pour donner le jugement de chaque maillon (Jarh wa Taʿdīl : Ibn Ḥajar, al-Dhahabī, avis des critiques avec source) ;
4. calcule un **verdict indicatif** de la chaîne (maillon le plus faible) à côté du jugement du recueil / d'al-Albānī ;
5. laisse un LLM (Claude) **uniquement** reformuler la requête et mettre en forme la réponse, sans jamais inventer une donnée.

## Architecture

```
question ──► [LLM: reformulations ar/en] ──► ChromaDB (e5 multilingue) ──► hadiths (top-k)
                                                                                │
                            SQL (PostgreSQL / SQLite) ◄── isnad_links ◄─────────┘
                            narrators · narrator_names · narrator_opinions
                                                                                │
                                              verdict de chaîne (grading.py) ◄──┘
                                                                                │
                                 [LLM: mise en forme, données uniquement] ──► réponse
```

| Composant | Rôle | Fichier |
|---|---|---|
| FastAPI | API + interface web | `hadith_bot/api.py`, `hadith_bot/static/index.html` |
| SQLAlchemy | schéma relationnel (PostgreSQL en prod, SQLite en dev) | `hadith_bot/models.py`, `hadith_bot/db.py` |
| ChromaDB + `intfloat/multilingual-e5-small` | index vectoriel des matn (segments arabes et anglais séparés) | `hadith_bot/vector.py` |
| SQLite FTS5 / PostgreSQL tsvector | index lexical BM25 + détection d'expression exacte | `hadith_bot/lexical.py` |
| Fusion RRF | vecteur + BM25 + expression contiguë (poids 1 / 1 / 2) | `retrieval.hybrid_search` |
| Parseur d'isnad | termes de transmission, تحويل (ح), co-rapporteurs, « عن أبيه » | `hadith_bot/isnad.py` |
| Appariement | nom d'isnad → notice (exact, flou, désambiguïsation maître/élève) | `hadith_bot/matching.py` |
| Jarh wa Taʿdīl | classification des formules + verdict de chaîne | `hadith_bot/grading.py` |
| Modèle local (MLX, Qwen 2.5 7B 4 bits) | comprend la question, génère des formulations « verbatim », trie la pertinence, extrait les réponses et les résumés ; ne note jamais | `hadith_bot/local_llm.py` |
| Claude (optionnel, `HADITH_LLM_BACKEND=anthropic`) | même rôle via l'API Anthropic | `hadith_bot/llm.py` |

### Données

| Source | Contenu | Licence / citation |
|---|---|---|
| [LK-Hadith-Corpus](https://github.com/ShathaTm/LK-Hadith-Corpus) (Leeds / King Saud) | 34 084 hadiths des six recueils, isnad et matn séparés, traduction anglaise, jugement (Bukhari relu manuellement ; autres livres segmentés automatiquement à 92 %) | citer Altammami, Atwell & Alsalka (IMAN 2019 ; LREC 2020) |
| [Itqan](https://github.com/R3GENESI5/Itqan) — `app/data/rijal/` | 115 735 notices de narrateurs fusionnées depuis 22 ouvrages classiques (Taqrīb, Tahdhīb al-Kamāl, Mīzān, al-Jarḥ wa-l-Taʿdīl, al-Thiqāt…), 217 762 variantes de noms, relations maîtres/élèves (AR-Sanad) | code MIT, textes du domaine public |
| Itqan — `src/external_narrators_db.json` | 1 524 narrateurs avec les avis détaillés de jarh/taʿdīl (critique, formule, référence de volume/page) | idem |

## Installation

```bash
uv sync --extra dev                       # Python 3.12, dépendances (torch/sentence-transformers inclus)
cp .env.example .env                      # ANTHROPIC_API_KEY=... (facultatif)
uv run python scripts/download_data.py    # corpus LK + base Itqan  (~260 Mo dans data/raw)
uv run python scripts/ingest_hadiths.py   # hadiths + extraction des isnads      (~1 min)
uv run python scripts/ingest_narrators.py # narrateurs (fusion des doublons) + avis (~35 s)
uv run python scripts/link_narrators.py   # appariement maillons ↔ narrateurs    (~25 s)
uv run python scripts/build_fts.py        # index lexical BM25                   (~10 s)
uv run python scripts/build_index.py      # embeddings ChromaDB (80k segments)   (~15 min CPU)
uv run uvicorn hadith_bot.api:app --port 8000
```

Après une évolution du parseur d'isnad : `scripts/reparse_isnads.py` puis `scripts/link_narrators.py`
(les identifiants de hadiths sont conservés, les index n'ont pas à être reconstruits).

```bash
uv run python scripts/eval_retrieval.py   # mini-jeu d'essai de la recherche (14 questions)
```

Interface : http://localhost:8000 · API : http://localhost:8000/docs

En ligne de commande :

```bash
uv run python -m hadith_bot.cli "la prière du voyageur" --no-llm
```

### PostgreSQL (production)

```bash
docker compose up -d db
export HADITH_DATABASE_URL=postgresql+psycopg://hadith:hadith@localhost:5432/hadith
# puis relancer les scripts d'ingestion
```

## API

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/ask` | `{question, k, use_llm, collections}` → hadiths, chaînes, jugements, verdicts, réponse |
| `GET` | `/hadith/{id}` · `/hadiths/{recueil}/{n°}` | fiche complète d'un hadith |
| `GET` | `/narrator/{id}` · `/narrator/{id}/hadiths` | notice, avis de jarh/taʿdīl, hadiths où il apparaît |
| `GET` | `/narrators/search?q=` | recherche de narrateur par nom |
| `GET` | `/health` | volumes chargés, état du LLM |

## Schéma SQL et requêtes utiles

```sql
-- jugement de chaque maillon d'un hadith
SELECT l.position, l.name_as_written, l.transmission_term, n.name_ar, n.grade_category, n.grade_ibn_hajar
FROM isnad_links l LEFT JOIN narrators n ON n.id = l.narrator_id
WHERE l.hadith_id = :id ORDER BY l.chain_no, l.position;

-- avis des critiques sur un narrateur
SELECT critic, opinion, kind, source_book FROM narrator_opinions WHERE narrator_id = :nid;

-- hadiths dont la chaîne contient un narrateur متروك ou كذاب
SELECT DISTINCT h.id FROM hadiths h JOIN isnad_links l ON l.hadith_id = h.id
JOIN narrators n ON n.id = l.narrator_id WHERE n.grade_rank <= 1;
```

Catégories (`narrators.grade_category` / `grade_rank`) : `companion` 6 · `thiqa` 5 · `saduq` 4 · `maqbul` 3 (à corroborer) · `daif` 2 · `matruk` 1 · `kadhdhab` 0 · `unknown` NULL. Les formules sont classées par `grading.classify_grade_text` (marātib d'Ibn Ḥajar) ; la seule mention dans *al-Thiqāt* d'Ibn Ḥibbān est ramenée à `saduq` (تساهل).

## Fonctionnement autonome (sans API)

Par défaut (`HADITH_LLM_BACKEND=local`), un modèle ouvert tourne sur la machine via MLX (Apple Silicon) : `mlx-community/Qwen2.5-7B-Instruct-4bit`, téléchargé une fois (~4,5 Go) dans le cache Hugging Face au premier lancement. Pipeline d'une question (≈ 30 à 60 s sur un M5) :

1. **Compréhension** : langue, intention (fait, règle, récit…), ce qu'il faut extraire, formulations arabes imitant le texte des hadiths (« تزوجني رسول الله وانا بنت ») et anglaises ;
2. **Recherche hybride** sur toutes les formulations (15 candidats) ;
3. **Tri** : le modèle ne garde que les hadiths qui contiennent l'information ;
4. **Extraction** : pour chaque hadith retenu, la réponse telle que le texte la donne, une étiquette de regroupement et un résumé ar/en ;
5. **Regroupement** des réponses identiques, puis **note /5 par réponse** calculée par `grading.score_topic` (jamais par le modèle) ;
6. Synthèse déterministe (gabarit dans la langue de la question) : le modèle n'écrit aucun texte libre, pour éviter les inventions.

Exemple : « عمر عائشة عندما تزوجت بالنبي » → « تزوجها وهي بنت ست وبنى بها وهي بنت تسع » 5/5 (Bukhari 5133, 5134, Muslim 3414…) et « بنت سبع… » 4/5 (Ibn Majah 1877, Abu Dawud…).

## Synthèse notée sur 5

Chaque réponse commence par une **synthèse** : la réponse courte à la question et un **degré de fiabilité de l'information** de 0 à 5, calculé par le système (jamais par le LLM) à partir des hadiths pertinents :

| Note | Libellé | Critère |
|---|---|---|
| 5 | Établi (ثابت) | Sahih al-Bukhari ou Sahih Muslim avec chaîne entièrement identifiée de narrateurs ثقة, ou plusieurs rapports authentiques indépendants (recueils ou Compagnons différents) |
| 4 | Authentique (صحيح) | jugé صحيح par le recueil / al-Albânî, chaîne cohérente avec ce jugement |
| 3 | Bon / acceptable (حسن) | jugé حسن, ou un narrateur صدوق يهم / مقبول, ou chaîne partiellement identifiée |
| 2 | Faible (ضعيف) | jugé ضعيف, ou narrateur faible dans la chaîne |
| 1 | Très faible / rejeté | narrateur متروك / كذاب, ou jugement منكر / شاذ / موضوع |
| 0 | Aucune base trouvée | aucun hadith pertinent dans les six recueils indexés |

Sans LLM, un hadith n'entre dans la synthèse que s'il contient les termes de la question (expression exacte, ou couverture pondérée IDF ≥ 0,6 incluant le terme le plus rare) ; si aucun résultat ne passe ce filtre, la note est « ? — pertinence non établie » plutôt qu'une note trompeuse. Avec le LLM, c'est lui qui désigne les hadiths pertinents (`relevant_hadith_ids`), la note reste calculée par le système.

Par hadith (`reliability`) : base = jugement du recueil ; l'analyse des narrateurs **relève** à 5 un hadith des Sahihayn dont tous les narrateurs sont identifiés ثقة, et **abaisse** d'un cran un hadith dont un narrateur faible est apparié avec certitude (divergence signalée). Au niveau de la question (`synthesis`) : les hadiths pertinents sont choisis par le LLM (sinon par le score de recherche), la note retenue est celle de la meilleure attestation, portée à 5 si deux rapports authentiques indépendants concordent. Les rapports موقوف / مقطوع sont signalés comme non attribués au Prophète ﷺ.

## Garde-fous contre les hallucinations

- Le LLM reçoit un JSON fermé (hadiths, chaînes, jugements) et la consigne de ne rien ajouter ; sans clé API, la réponse est produite de façon déterministe (`retrieval.format_plain`).
- Chaque maillon expose sa méthode d'appariement (`exact`, `exact+ctx`, `fuzzy`, `relative`, `ambiguous`, `none`) et son score ; les non identifiés sont listés explicitement.
- Le verdict de chaîne est libellé « indicatif » et accompagné du jugement du recueil ; l'application ne délivre aucune fatwa.

## État des données chargées (2026-09-16)

| Indicateur | Valeur |
|---|---|
| Hadiths (6 recueils) | 34 084 |
| Maillons d'isnad extraits | 207 000 (≈ 6 par hadith) |
| Maillons liés à une notice | 95,6 % (exact 25 %, exact + contexte maître/élève 42 %, homonymes résolus « ambiguous » 23 %, références relatives 3 %) |
| Narrateurs après fusion des doublons | 94 396 (dont 10 397 Compagnons) |
| Avis de jarh/taʿdīl sourcés | 40 514 (1 521 narrateurs) |
| Recherche (top-5, `scripts/eval_retrieval.py`) | hybride 10/14 ; les 4 échecs sont des paraphrases fr/en sans LLM, cas prévu pour l'expansion de requête |

## Limites connues

- Segmentation isnad/matn automatique (hors Bukhari) : ~8 % d'erreurs héritées du corpus.
- Homonymes (سفيان، حماد…) : la désambiguïsation s'appuie sur les relations maître/élève d'AR-Sanad, sur la kunya/le nom du père (« ابن عمر ») et sur la position (dernier maillon = Compagnon) ; en cas d'ambiguïté résiduelle le maillon est marqué `ambiguous` (ex. « سفيان » chez al-Ḥumaydī reste attribué à al-Thawrī faute de relation enregistrée, les deux étant ثقة).
- Sans clé Anthropic, les questions en français ne sont pas traduites : la recherche repose alors sur le petit modèle multilingue e5 et le BM25 (bon en arabe/anglais). Un modèle plus fort (`HADITH_EMBEDDING_MODEL=BAAI/bge-m3`) améliore le français au prix d'une indexation plus longue.
- Fusion de doublons Itqan par clé « X بن Y بن Z » + compatibilité des dates : deux homonymes sans date de décès peuvent être fusionnés à tort.
- Jonction après تحويل (ح) inférée quand « كلاهما عن » est absent.
- Les jugements « استنباط من الأسانيد » d'Itqan (inférés, non textuels) sont affichés comme tels et non comptés.

## Tests

```bash
uv run pytest -q
```
