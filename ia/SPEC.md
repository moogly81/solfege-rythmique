# Spécification technique : générateur du cahier de rythme

Document autosuffisant : avec `PEDAGOGIE.md`, `NOTATION.md` et `cahier.txt`, il suffit pour régénérer toute l'application **en une fois** (voir `ia/PROMPT.md`). Le code n'a pas à être identique à l'existant ; le comportement décrit ici, si.

Priorité en cas de conflit : `PEDAGOGIE.md` > `NOTATION.md` > ce fichier.

## 1. But

Transformer `cahier.txt` (format : `NOTATION.md`) en `cahier_rythme.pdf` : une leçon = une page A4, portée de rythme à 1 ligne, gravure MuseScore.

Pipeline, une étape par module, chacune testable seule :

```
cahier.txt → modèle (dataclasses) → vérification rythmique → 1 MusicXML par leçon (build/page_NN.musicxml)
          → PDF par page (MuseScore 4 CLI, un seul appel) → fusion qpdf → cahier_rythme.pdf
```

## 2. Contraintes générales

- Python ≥ 3.11, **bibliothèque standard uniquement** à l'exécution.
- Outils externes à l'exécution :
  - MuseScore 4 (`/Applications/MuseScore 4.app/Contents/MacOS/mscore`, sinon `mscore`/`musescore` dans le PATH) ; testé avec **4.7.x** (le style `.mss` porte `version="4.70"`) ; la CI n'en dispose pas et ne rend jamais de PDF ;
  - `qpdf` (PATH ou `/opt/homebrew/bin/qpdf`).
  - Surcharge : variables d'env `MSCORE`, `QPDF`. Si la variable est définie mais pointe sur un chemin inexistant : erreur explicite, pas de repli silencieux.
- Outils de vérification seulement (pas requis pour générer) : `pdftoppm` (poppler) pour le contrôle visuel.
- Installation (macOS) : MuseScore 4 depuis musescore.org, `brew install qpdf poppler uv`, puis `uv venv && uv pip install -e ".[dev]"`. Le `.venv/` du dépôt doit contenir `pytest` et `ruff`.
- Code, messages, docs : **français** (messages avec accents et guillemets « »).
- Erreurs utilisateur = exceptions `SolfegeError` (sous-classes `CahierError`, `RenduError`) ; seul le CLI les transforme en message sur stderr + code 1, sans trace Python.

## 3. Paquet `solfege/`

| Module | Rôle |
|---|---|
| `erreurs.py` | `SolfegeError`, `CahierError`, `RenduError` |
| `config.py` | chemins par défaut (`cahier.txt`, `build/`, `cahier_rythme.pdf`), chiffrage par défaut `4/4`, candidats d'outils, mise en page, style MuseScore |
| `cahier.py` | texte → `Cahier(source, chapters)` ⊃ `Chapter(number, title, lessons)` ⊃ `Lesson(number "N.M", title, where, instruction, time, exercises)` ⊃ `Exercise(number "N.M.K", time, lines: [SourceLine(text, where, syllables, syllables_where)])`. Structure seulement |
| `rythme.py` | symboles, `parse_time`, `parse_line`, `parse_syllables`, `parse_exercise`, `check_header`, `check(cahier) -> list[str]`, `compute_beams` |
| `largeurs.py` | largeurs des glyphes de la police Edwin (Roman/Bold/Italic, millièmes d'em), `largeur_mm(texte, police, pt)`, `LARGEUR_UTILE_MM` |
| `musicxml.py` | `lesson_to_musicxml(chapter, lesson) -> str`, fonction pure |
| `rendu.py` | `find_tool`, `render_pdfs` (MuseScore), `page_count`, `overflow_warnings`, `merge_pdfs` (qpdf) |
| `cli.py` | `main(argv) -> int` |
| `__main__.py` | `python -m solfege` |

Raccourci historique à la racine : `solfege_rythmique.py` appelle `solfege.cli.main`.

### 3.1 Lecture (`cahier.py`)

Suit `NOTATION.md` § 3.

- Lecture en `utf-8-sig` : un BOM (Bloc-notes Windows) est ignoré.
- Numérotation automatique par ordre d'apparition ; le numéro écrit après « Chapitre » est ignoré.
- `where` = « cahier.txt, ligne 12 » (nom de fichier réel).
- Une ligne « décalée » commence par au moins un espace, une tabulation ou une espace insécable (la doc dit « 2 espaces » ; on est tolérant).
- `Consigne :` et `Mesure :` exigent le « : » (sinon : « « Mesure 3/4 » doit être suivi de « : » (exemple : « Mesure : ... ») ») ; `Consigne :` vide accepté ; `Mesure :` refusée après le 1er exercice de la leçon (« doit être placée avant le 1er exercice »). Deux `Consigne :` : la dernière gagne.
- Erreurs levées immédiatement :
  - pas de chapitre ;
  - `##` hors chapitre ;
  - texte hors leçon ;
  - ligne non comprise (avec rappel : « un exercice commence par « - », sa 2e ligne par 2 espaces ou une tabulation ») ;
  - leçon sans exercice ;
  - exercice de plus de 2 lignes ;
  - deux lignes de syllabes `=` sous la même ligne.
- Ligne `  = …` : syllabes attachées à la ligne de rythme précédente (`SourceLine.syllables`, `syllables_where`) ; ne compte pas comme une ligne.

### 3.2 Rythme (`rythme.py`)

- 12 divisions MusicXML par noire (divisible par 3 et par 4).
- Symbole → (durée en divisions, type MusicXML, silence ?, pointé ?) :
  - `r` 48 whole, `b.` 36 half pointée, `b` 24 half, `n.` 18 quarter pointée, `n` 12 quarter ;
  - `c.` 9 eighth pointée, `c` 6 eighth, `t` 4 eighth (triolet), `d` 3 16th ;
  - silences : `p` = mesure entière (whole), `dp` 24 half, `s` 12 quarter, `ds` 6 eighth.
- Chiffrages acceptés : `N/4` uniquement, 1 ≤ N ≤ 12 (« chiffrage invalide « 0/4 » (de 1 à 12 temps par mesure) »).
- Vérifications de `NOTATION.md` § 4 :
  - mesure vide (« mesure 2 : mesure vide (deux barres « | » à la suite ?) ») ;
  - symbole inconnu ;
  - `p` seul dans sa mesure ;
  - triolet = 3 `t` consécutifs commençant sur un temps ;
  - durée de mesure juste.
- Syllabes (`parse_syllables`) renvoie, par mesure, **une entrée par symbole** (`None` = rien à afficher) :
  - même nombre de mesures que le rythme ;
  - une syllabe par note ; un silence n'en a pas, sauf une syllabe entre parenthèses `(chut)` placée à sa position (le texte affiché est sans parenthèses) ;
  - erreurs : « … (syllabes de l'exercice N.M.K), mesure 2 (1 2) : 2 syllabes pour 3 notes » (compte des syllabes hors parenthèses), « syllabe vide « - » », « parenthèse non fermée « (chut » », « « (chut) » : une syllabe entre parenthèses va sous un silence ».
- `check` renvoie **toutes** les erreurs (au plus une par ligne), format exact : `cahier.txt, ligne 52 (exercice 2.1.3), mesure 2 (b n n) : 4 temps au lieu de 3`.
- **En-tête** (`check_header`) : les 3 lignes (« Chapitre N · titre » 12 pt romain, « N.M  titre » 22 pt gras, consigne 13 pt italique ; tailles dans `config.py`) doivent tenir dans la largeur utile (page − 2 marges = 180 mm). Largeur = somme des avances de glyphes de la police **Edwin** (celle de MuseScore 4, tables `hmtx` extraites de `Edwin-Roman/Bold/Italic.otf` dans `solfege/largeurs.py`, caractère inconnu = largeur d'un « n ») × taille × 25,4/72. Calibrage : une consigne de 13 pt mesurée 163 mm dans le PDF donne 164 mm estimés. Message : « cahier.txt, ligne 72 : le titre de la leçon est trop large pour la page (≈ 219 mm, maximum 180 mm) : le raccourcir ». Sans cette vérification, MuseScore laisse le texte déborder de la page et décale les autres lignes de l'en-tête.
- Ligatures (`compute_beams`), groupées par temps :
  - un groupe commence sur une note ligaturable (croche, double, `t`, non-silence) posée **sur un temps** ou après un élément non ligaturable ; il continue tant que les notes ligaturables suivantes ne tombent pas sur un temps. Une valeur qui chevauche deux temps (`c c. d`) garde donc la suite dans son groupe ;
  - niveau 1 sur tout le groupe ;
  - niveau 2 sur les suites de doubles ; une double isolée dans un groupe = `forward hook`, ou `backward hook` si elle est la dernière du groupe ;
  - `c n c`, `n. c`, `c s c` : aucune ligature.

### 3.3 MusicXML (`musicxml.py`)

Choix validés par essais avec MuseScore 4.7 ; ne pas les changer sans revérifier le rendu.

- **Instrument** :
  - partie unique, `part-name print-object="no"` ;
  - `score-instrument` « Hand Clap », `midi-unpitched` 40, canal 10 ;
  - chaque note : `<unpitched>` B4 + `<instrument id=…>`, hampe en haut sauf ronde.
  - Sans instrument non accordé, MuseScore importe une portée de piano et place les notes sous la ligne.
- **Portée** : `staff-lines` 1, clé `percussion`, armure masquée.
- **Chaque ligne de rythme** (1re et 2e ligne d'un exercice) commence un système : `<print new-system="yes"/>` sur sa 1re mesure, sauf la 1re mesure de la page.
- **Chaque exercice** :
  - chiffrage réémis sur sa 1re mesure ; la 1re mesure de la page porte aussi `divisions` 12, `key print-object="no"`, `staff-details/staff-lines` 1, `clef/sign` percussion ;
  - repère `<direction placement="above">` + `<rehearsal enclosure="rectangle">N.M.K</rehearsal>` ;
  - double barre finale `<barline location="right"><bar-style>light-heavy</bar-style></barline>` sur sa dernière mesure.
- **Ordre des enfants de `<note>`** (MusicXML est strict, MuseScore refuse sinon) : `rest`|`unpitched`, `duration`, `instrument` (notes seulement), `voice` (toujours 1), `type`, `dot`, `time-modification`, `stem` (`up`, notes sauf ronde), `beam`, `notations`, `lyric`.
- **En-tête** :
  - `<work><work-title>N.M  titre</work-title></work>` (nom du document dans MuseScore ; non imprimé) ;
  - **un seul** `<credit page="1">` de type `title`, avec 3 `credit-words` séparés par `&#10;` : « Chapitre N · titre » (12), « N.M  titre » (22, gras), consigne (13, italique) ; le 1er porte `justify="center" halign="center" valign="top" default-x="{pw/2}" default-y="{ph - marge}"` (dixièmes, arrondis à l'entier) ;
  - plusieurs credits distincts se chevauchent.
- **Syllabes** : `<lyric number="1"><syllabic>single|begin|middle|end</syllabic><text>` en fin de note ; un tiret final (`qua-`) = la syllabe continue (begin/middle), tiret retiré du texte ; `_` → espace (« ron-de_lon-gue » sous une ronde) ; une syllabe de silence `(chut)` se pose sur le `<note>` du silence, MuseScore l'affiche sous le silence.
- **Triolet** : `time-modification` 3:2 ; `tuplet start` sur le 1er `t` et `stop` sur le 3e, `bracket="no"` (le 3 s'affiche sur la ligature).
- **Silences** :
  - `p` = `<rest measure="yes"/>`, durée = mesure ;
  - toujours les glyphes MuseScore, jamais de dessin maison.
- **Mise en page** (toutes les valeurs dans `config.py`) :
  - A4 (210 × 297 mm), marges 15 mm ;
  - `scaling` : 8,5 mm pour 40 dixièmes (1 dixième = 0,2125 mm ; page 988 × 1398 dixièmes) ;
  - `system-distance` 140, `top-system-distance` 150.

### 3.4 Rendu (`rendu.py`)

- `find_tool(env_var, candidats)` : variable d'env si définie (erreur si son chemin n'existe pas : « qpdf introuvable : la variable QPDF pointe sur « … », qui n'existe pas. »), sinon 1er candidat existant (`Path.exists()` ou `shutil.which`), sinon « Outil introuvable (MSCORE) : MuseScore 4. Installez-le (…) ou définissez MSCORE. ».
- Tout `subprocess.run` passe par un enrobage qui transforme `OSError` (outil non exécutable, permission) en `RenduError` « Impossible de lancer « … » : … ». Jamais de trace Python pour l'utilisateur.
- Un seul appel pour toutes les pages : `mscore -S <style.mss absolu> -j <job.json absolu>`. Le job est un tableau JSON :
  ```json
  [{"in": "/abs/build/page_01.musicxml", "out": "/abs/build/page_01.pdf"}, …]
  ```
  La sortie (stdout + stderr) va dans `build/mscore.log`. Tous les fichiers sont écrits/lus en UTF-8 explicitement.
- Supprimer les anciens `build/page_*.pdf` avant l'export, pour ne jamais fusionner de pages périmées.
- `style.mss` (MuseScore 4, `<museScore version="4.70"><Style>…`) :
  - `spatium` = 8,5 / 4 ;
  - `showMeasureNumber` 0 : `<measure-numbering>` du MusicXML est ignoré ;
  - `minSystemDistance` 9, `maxSystemDistance` 30, `enableVerticalSpread` 1 ;
  - `minMeasureWidth` 6, `lastSystemFillLimit` 0 ;
  - `genCourtesyTimesig` 0 : pas de chiffrage de courtoisie ;
  - `lyricsMinDistance` 1.2, `lyricsDashForce` 1 : sinon les syllabes des doubles se collent (« qua-tredou-bles »).
- **Bug connu** : MuseScore 4.7.5 fait un SIGABRT (`mutex lock failed`) dans `exit()` **après** avoir écrit les PDF. Le succès se juge donc sur la présence des PDF, pas sur le code retour. Si le code retour est ≠ 0 et que tout est là : note informative sur **stderr** (« Note : MuseScore a quitté avec le code -6 après export (bug connu à la fermeture, sans impact). »). PDF manquant : `RenduError` « MuseScore n'a pas produit : … (voir build/mscore.log) ».
- **Débordement** : `page_count(pdf)` via `qpdf --show-npages` ; `overflow_warnings(pdfs, numéros)` renvoie « Attention : la leçon 4.3 déborde (2 pages au lieu de 1) : raccourcir des lignes. » pour chaque PDF de page ≠ 1 page.
- Fusion : `qpdf --empty --pages build/page_*.pdf -- cahier_rythme.pdf` ; code retour ≠ 0 → `RenduError` avec le stderr de qpdf.

### 3.5 CLI (`cli.py`)

- Commande : `python3 -m solfege [check|xml|pdf]`, étape finale, `pdf` par défaut.
- Options : `--cahier`, `--build`, `--output`.
- Enchaînement :
  1. lecture ;
  2. `check`, qui lève toutes les erreurs jointes par `\n` ;
  3. écriture de `build/page_NN.musicxml`, après suppression des anciens ;
  4. rendu, avertissements de débordement sur stderr, puis fusion.
- Messages de fin (stdout) :
  - `cahier.txt : OK (8 chapitres, 33 leçons)` ;
  - `MusicXML écrits dans build/ (33 pages)` ;
  - `PDF généré : cahier_rythme.pdf (33 pages)`.
  - (nombres = ceux du cahier lu, jamais codés en dur).
- Codes de retour : 0 ; 1 = erreur (`SolfegeError` sur stderr, aucun fichier créé si l'erreur est dans le cahier) ; 2 = PDF produit mais au moins une leçon déborde.

## 4. Qualité

- `pyproject.toml` (setuptools ≥ 80) :
  - projet `solfege`, `readme = "README.md"`, `requires-python >= 3.11`, `dependencies = []`, extra `dev` = `pytest` et `ruff` **épinglés** (`==`), script `solfege = "solfege.cli:main"`, `[tool.setuptools] packages = ["solfege"]` ;
  - ruff : longueur 120, cible py311, règles `E F W I B UP SIM RUF`, ignorer `RUF001-003` (typographie française) ; `per-file-ignores` : `solfege/musicxml.py` et `solfege/largeurs.py` = `E501` (gabarit MusicXML aux lignes longues ; tables de glyphes) ;
  - pytest : `testpaths = ["tests"]`, `addopts = "-ra --strict-markers"`, marqueur `rendu`.
- Tests `tests/` (paquet : `__init__.py` ; `conftest.py` = chemins `ROOT`, `CAHIER_PATH`, `PEDAGOGIE_PATH`, `GOLDEN_DIR` + option `--regenerer-golden`) :
  - `test_cahier.py` : structure, numérotation, chiffrage par exercice, chaque erreur de structure avec son message exact, BOM, indentation (espaces, tabulation), `Consigne`/`Mesure` sans « : », `Mesure` après un exercice ;
  - `test_rythme.py` : largeur de l'en-tête (titre et consigne trop larges, calibrage 161–166 mm), durées, chiffrages (`0/4`, `-3/4`, `13/4`, `6/8`), syllabes (compte, mesures, `(chut)`, syllabe vide, parenthèses), chaque erreur de rythme (en 2/4, 3/4, 4/4), mesure vide, triolets, `check` qui renvoie plusieurs erreurs (messages complets), ligatures (`c c c c`, `c d d`, `d d c`, `c. d`, `t t t`, `c c. d`, silence qui coupe un groupe, `c n c`/`n. c` sans ligature) ;
  - `test_musicxml.py` : XML bien formé (`xml.etree`), 1 ligne, clé percussion, armure masquée, instrument et `unpitched` sur chaque note (pas sur les silences), hampes `up` sauf ronde, **ordre des enfants de `<note>`**, repères N.M.K encadrés, `new-system`, double barre, un seul credit (3 tailles), `work-title`, mise en page A4, triolet (`bracket="no"`), pause de mesure, échappement des `&` et `<`, syllabes (`syllabic`, `_`, silences sans syllabe, `(chut)`) ;
  - `test_cli.py` : `check` et `xml` sur un cahier temporaire, code 1 et message sans trace, aucun fichier créé en cas d'erreur, nettoyage des anciens fichiers ; `find_tool` (absent, variable valide, variable fausse) ; **rendu simulé** (`monkeypatch` de `subprocess.run`) : un seul appel MuseScore avec chemins absolus, suppression des anciens PDF, code retour ≠ 0 toléré (note sur stderr), PDF manquant, échec qpdf, avertissement de débordement, `OSError` ; `test_pdf_complet` marqué `rendu`, ignoré si MuseScore ou qpdf manque (via `find_tool`), 2 leçons, vérifie 1 page par PDF de page et 2 pages au total ;
  - `test_golden.py` : `tests/golden/exemple.txt` (tous les symboles, 3 chiffrages, syllabes, `(chut)`, triolet, 2 leçons) doit donner **octet pour octet** `tests/golden/exemple_NN.musicxml` (versionnés). C'est la référence de « comportement identique » lors d'un refactor ou d'une régénération ; `pytest tests/test_golden.py --regenerer-golden` la met à jour après un changement de rendu voulu ;
  - `test_contenu.py` : le vrai `cahier.txt` passe `check` ; il suit la « Progression actuelle » de PEDAGOGIE.md, **lue dans le fichier** ; syllabes sur le 1er exercice des leçons listées dans « Leçons avec syllabes » **et seulement celles-là** ; 4 à 6 exercices et 6 à 10 lignes par leçon, consigne présente et ≤ 95 caractères, au moins 2 symboles distincts par leçon, pas plus de 8 `d` d'affilée (barres comprises). Un motif introuvable donne un message clair, pas une `AttributeError`.
- Grammaire exacte des lignes de PEDAGOGIE.md lues par `test_contenu.py` (regex, `re.MULTILINE`) :
  - `^## Progression actuelle \((\d+) chapitres, (\d+) pages\)$` ;
  - une ligne par chapitre : `^\d+\. \*\*(.+?)\*\* : (.+)$`, titre = celui du chapitre dans `cahier.txt`, leçons séparées par ` · ` (espace, point médian, espace) ;
  - `^Leçons avec syllabes \(1er exercice\) : (.+)\.$`, numéros séparés par `, `.
- CI `.github/workflows/ci.yml` :
  - sur push `main` et PR, `permissions: contents: read` ;
  - matrice Python `"3.11"` et `"3.x"` (dernière stable) ;
  - `actions/checkout@v7`, `actions/setup-python@v7`, `astral-sh/setup-uv@v7` (tags majeurs, mis à jour par Dependabot) ;
  - `uv pip install --system -e ".[dev]"`, `ruff check .`, `ruff format --check .`, `python -m solfege check`, `pytest` (pas de MuseScore : tests `rendu` ignorés).
- `.github/dependabot.yml` : `pip` et `github-actions`, hebdomadaire, un groupe par écosystème.
- `.gitignore` :
  - `build/`, `__pycache__/`, `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, `.claude/`, `.DS_Store` ;
  - `cahier_rythme.pdf` et `tests/golden/` restent versionnés.

## 5. Documentation à produire / garder

- `README.md` : 3 lignes (modifier, générer, développer) + tableau d'installation.
- `TODO.md` : pistes non réalisées (liaison, levée, point d'orgue, tempo, LilyPond) ; à garder, ne pas régénérer.
- `CLAUDE.md` : consignes pour l'agent (renvoie à ce fichier, environnement, vérifications).
- `PEDAGOGIE.md`, `NOTATION.md`, `cahier.txt` : **entrées**, à ne pas réécrire lors d'une régénération (sauf pour corriger une commande obsolète).

## 6. Critères d'acceptation

1. `ruff check . && ruff format --check . && pytest` : tout vert.
2. `python3 -m solfege` rend le code 0 (pas d'avertissement « déborde ») et produit `cahier_rythme.pdf` d'autant de pages que la « Progression actuelle » de PEDAGOGIE.md (une par leçon), avec exactement 1 page par `build/page_NN.pdf` (`qpdf --show-npages`). Sinon la leçon déborde : ajuster la mise en page, **pas** le contenu.
3. Contrôle visuel : `pdftoppm -png -r 50 -f N -l N cahier_rythme.pdf "$TMPDIR/x"`, sur au moins la page 1, la dernière et chaque leçon de « Leçons avec syllabes » (PEDAGOGIE.md). Vérifier :
   - en-tête sur 3 lignes, cadres N.M.K, une ligne par exercice ;
   - notes **sur** la ligne, silences corrects ;
   - points, « 3 » des triolets, ligatures et crochets des doubles ;
  - syllabes lisibles, sous leurs notes, sans retour à la ligne imprévu ;
   - chiffrages qui changent, aucun numéro de mesure.
4. Un `cahier.txt` avec une faute affiche le message au format de `NOTATION.md` et ne crée aucun fichier.
5. `pytest tests/test_golden.py` passe **sans** `--regenerer-golden` : le MusicXML produit est identique à la référence versionnée. Si le rendu a changé volontairement, régénérer la référence et le dire dans le rapport.
