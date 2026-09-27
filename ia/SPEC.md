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
- Outils externes : MuseScore 4 (`/Applications/MuseScore 4.app/Contents/MacOS/mscore`, sinon `mscore`/`musescore` dans le PATH), `qpdf` (PATH ou `/opt/homebrew/bin/qpdf`). Surcharge : variables d'env `MSCORE`, `QPDF`.
- Code, messages, docs : **français** (messages avec accents et guillemets « »).
- Erreurs utilisateur = exceptions `SolfegeError` (sous-classes `CahierError`, `RenduError`) ; seul le CLI les transforme en message sur stderr + code 1, sans trace Python.

## 3. Paquet `solfege/`

| Module | Rôle |
|---|---|
| `erreurs.py` | `SolfegeError`, `CahierError`, `RenduError` |
| `config.py` | chemins par défaut (`cahier.txt`, `build/`, `cahier_rythme.pdf`), chiffrage par défaut `4/4`, candidats d'outils, mise en page, style MuseScore |
| `cahier.py` | texte → `Cahier(source, chapters)` ⊃ `Chapter(number, title, lessons)` ⊃ `Lesson(number "N.M", title, where, instruction, time, exercises)` ⊃ `Exercise(number "N.M.K", time, lines: [SourceLine(text, where)])`. Structure seulement |
| `rythme.py` | symboles, `parse_line`, `check(cahier) -> list[str]`, `compute_beams` |
| `musicxml.py` | `lesson_to_musicxml(chapter, lesson) -> str`, fonction pure |
| `rendu.py` | MuseScore puis qpdf |
| `cli.py` | `main(argv) -> int` |
| `__main__.py` | `python -m solfege` |

Raccourci historique à la racine : `solfege_rythmique.py` appelle `solfege.cli.main`.

### 3.1 Lecture (`cahier.py`)

Suit `NOTATION.md` § 3.

- Numérotation automatique par ordre d'apparition ; le numéro écrit après « Chapitre » est ignoré.
- `where` = « cahier.txt, ligne 12 » (nom de fichier réel).
- Erreurs levées immédiatement :
  - pas de chapitre ;
  - `##` hors chapitre ;
  - texte hors leçon ;
  - ligne non comprise (avec rappel : « un exercice commence par « - », sa 2e ligne par 2 espaces ») ;
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
- Chiffrages acceptés : `N/4` uniquement.
- Vérifications de `NOTATION.md` § 4 :
  - symbole inconnu ;
  - `p` seul dans sa mesure ;
  - triolet = 3 `t` consécutifs commençant sur un temps ;
  - durée de mesure juste.
- Syllabes (`parse_syllables`) : même nombre de mesures que le rythme, une syllabe par note non-silence ; message « … (syllabes de l'exercice N.M.K), mesure 2 (1 2) : 2 syllabes pour 3 notes ».
- `check` renvoie **toutes** les erreurs (au plus une par ligne), format exact : `cahier.txt, ligne 52 (exercice 2.1.3), mesure 2 (b n n) : 4 temps au lieu de 3`.
- Ligatures, groupées par temps :
  - niveau 1 sur les croches/doubles/triolets consécutifs (non-silences) d'un même temps ;
  - niveau 2 sur les suites de doubles ; une double isolée dans un groupe = `forward hook`, ou `backward hook` si elle est la dernière du groupe.

### 3.3 MusicXML (`musicxml.py`)

Choix validés par essais avec MuseScore 4.7 ; ne pas les changer sans revérifier le rendu.

- **Instrument** :
  - partie unique, `part-name print-object="no"` ;
  - `score-instrument` « Hand Clap », `midi-unpitched` 40, canal 10 ;
  - chaque note : `<unpitched>` B4 + `<instrument id=…>`, hampe en haut sauf ronde.
  - Sans instrument non accordé, MuseScore importe une portée de piano et place les notes sous la ligne.
- **Portée** : `staff-lines` 1, clé `percussion`, armure masquée.
- **Chaque exercice** :
  - nouvelle ligne (`<print new-system="yes"/>`, sauf la 1re mesure de la page) ;
  - chiffrage réémis ;
  - repère `<rehearsal enclosure="rectangle">N.M.K</rehearsal>` au-dessus ;
  - double barre finale `light-heavy`.
- **En-tête** :
  - **un seul** `<credit>` de type `title`, avec 3 `credit-words` séparés par `&#10;` : « Chapitre N · titre » (12), « N.M  titre » (22, gras), consigne (13, italique) ;
  - plusieurs credits distincts se chevauchent.
- **Syllabes** : `<lyric number="1"><syllabic>single|begin|middle|end</syllabic><text>` en fin de note ; un tiret final (`qua-`) = la syllabe continue (begin/middle), tiret retiré du texte.
- **Triolet** : `time-modification` 3:2 ; `tuplet start` sur le 1er `t` et `stop` sur le 3e, `bracket="no"` (le 3 s'affiche sur la ligature).
- **Silences** :
  - `p` = `<rest measure="yes"/>`, durée = mesure ;
  - toujours les glyphes MuseScore, jamais de dessin maison.
- **Mise en page** :
  - A4 (210 × 297 mm), marges 15 mm ;
  - `scaling` : 8,5 mm pour 40 dixièmes ;
  - `system-distance` 140, `top-system-distance` 150.

### 3.4 Rendu (`rendu.py`)

- Un seul appel pour toutes les pages : `mscore -S build/style.mss -j build/job.json` (job = liste `{"in", "out"}` en chemins absolus). La sortie va dans `build/mscore.log`.
- Supprimer les anciens `build/page_*.pdf` avant l'export, pour ne jamais fusionner de pages périmées.
- `style.mss` (MuseScore 4, `<museScore version="4.70"><Style>…`) :
  - `spatium` = 8,5 / 4 ;
  - `showMeasureNumber` 0 : `<measure-numbering>` du MusicXML est ignoré ;
  - `minSystemDistance` 9, `maxSystemDistance` 30, `enableVerticalSpread` 1 ;
  - `minMeasureWidth` 6, `lastSystemFillLimit` 0 ;
  - `genCourtesyTimesig` 0 : pas de chiffrage de courtoisie ;
  - `lyricsMinDistance` 1.2, `lyricsDashForce` 1 : sinon les syllabes des doubles se collent (« qua-tredou-bles »).
- **Bug connu** : MuseScore 4.7.5 fait un SIGABRT (`mutex lock failed`) dans `exit()` **après** avoir écrit les PDF. Le succès se juge donc sur la présence des PDF, pas sur le code retour. Si le code retour est ≠ 0 et que tout est là : simple note informative.
- Fusion : `qpdf --empty --pages build/page_*.pdf -- cahier_rythme.pdf`.

### 3.5 CLI (`cli.py`)

- Commande : `python3 -m solfege [check|xml|pdf]`, étape finale, `pdf` par défaut.
- Options : `--cahier`, `--build`, `--output`.
- Enchaînement :
  1. lecture ;
  2. `check`, qui lève toutes les erreurs jointes par `\n` ;
  3. écriture de `build/page_NN.musicxml`, après suppression des anciens ;
  4. rendu, puis fusion.
- Messages de fin :
  - `cahier.txt : OK (8 chapitres, 31 leçons)` ;
  - `MusicXML écrits dans build/ (31 pages)` ;
  - `PDF généré : cahier_rythme.pdf (31 pages)`.
  - (nombres = ceux du cahier lu, jamais codés en dur).

## 4. Qualité

- `pyproject.toml` (setuptools) :
  - projet `solfege`, `dependencies = []`, extra `dev` = `pytest` et `ruff` **épinglés** (`==`), script `solfege = "solfege.cli:main"` ;
  - ruff : longueur 120, cible py311, règles `E F W I B UP SIM RUF`, ignorer `RUF001-003` (typographie française) ;
  - pytest : `--strict-markers`, marqueur `rendu`.
- Tests `tests/` :
  - `test_cahier.py` : structure, numérotation, chiffrage par exercice, chaque erreur de structure avec son message ;
  - `test_rythme.py` : durées, syllabes (compte, mesures), chaque erreur de rythme (en 2/4, 3/4, 4/4), triolets, `check` qui renvoie plusieurs erreurs, ligatures (`c c c c`, `c d d`, `d d c`, `c. d`, `t t t`, silence qui coupe un groupe) ;
  - `test_musicxml.py` : XML bien formé (`xml.etree`), 1 ligne, clé percussion, instrument sur chaque note, repères N.M.K, `new-system`, double barre, un seul credit, triolet, pause de mesure, échappement des `&` et `<`, syllabes (`syllabic`, silences sans syllabe) ;
  - `test_cli.py` : `check` et `xml` sur un cahier temporaire, code 1 et message sans trace en cas d'erreur, nettoyage des anciens fichiers ; `test_pdf_complet` marqué `rendu`, ignoré si MuseScore ou qpdf manque, vérifie 1 page par PDF de page ;
  - `test_contenu.py` : le vrai `cahier.txt` passe `check` ; il suit la « Progression actuelle » de PEDAGOGIE.md, **lue dans le fichier** (nombre de pages, titres des chapitres, nombre de leçons par chapitre = éléments séparés par « · ») ; syllabes sur le 1er exercice des leçons listées dans « Leçons avec syllabes » ; 4 à 6 exercices et 6 à 10 lignes par leçon, consigne présente, au moins 2 symboles distincts par leçon (notes ou silences).
- CI `.github/workflows/ci.yml` :
  - sur push `main` et PR, `permissions: contents: read` ;
  - matrice Python 3.11 et dernière stable ;
  - `pip install -e ".[dev]"`, `ruff check .`, `ruff format --check .`, `python -m solfege check`, `pytest` (pas de MuseScore : tests `rendu` ignorés).
- `.github/dependabot.yml` : `pip` et `github-actions`, hebdomadaire, un groupe par écosystème.
- `.gitignore` :
  - `build/`, `__pycache__/`, `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/` ;
  - `cahier_rythme.pdf` reste versionné.

## 5. Documentation à produire / garder

- `README.md` : 3 lignes (modifier, générer, développer).
- `CLAUDE.md` : consignes pour l'agent (renvoie à ce fichier, environnement, vérifications).
- `PEDAGOGIE.md`, `NOTATION.md`, `cahier.txt` : **entrées**, à ne pas réécrire lors d'une régénération (sauf pour corriger une commande obsolète).

## 6. Critères d'acceptation

1. `ruff check . && ruff format --check . && pytest` : tout vert.
2. `python3 -m solfege` produit `cahier_rythme.pdf` d'autant de pages que la « Progression actuelle » de PEDAGOGIE.md (une par leçon), avec exactement 1 page par `build/page_NN.pdf` (`qpdf --show-npages`). Sinon la leçon déborde : ajuster la mise en page, **pas** le contenu.
3. Contrôle visuel : `pdftoppm -png -r 50 -f N -l N cahier_rythme.pdf "$TMPDIR/x"`, sur au moins la page 1, la dernière et chaque leçon de « Leçons avec syllabes » (PEDAGOGIE.md). Vérifier :
   - en-tête sur 3 lignes, cadres N.M.K, une ligne par exercice ;
   - notes **sur** la ligne, silences corrects ;
   - points, « 3 » des triolets, ligatures et crochets des doubles ;
  - syllabes lisibles, sous leurs notes, sans retour à la ligne imprévu ;
   - chiffrages qui changent, aucun numéro de mesure.
4. Un `cahier.txt` avec une faute affiche le message au format de `NOTATION.md` et ne crée aucun fichier.
