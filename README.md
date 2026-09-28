# Cahier de solfège rythmique

Ce dépôt génère un cahier d'exercices (33 pages A4) pour apprendre à une enfant de 6 ans à lire des rythmes (notes, silences, mesures) : `cahier.txt` → LilyPond → PDF.

- Modifier le contenu : `cahier.txt`, format dans [NOTATION.md](NOTATION.md), règles dans [PEDAGOGIE.md](PEDAGOGIE.md).
- Générer : `python3 -m solfege` (vérifier seulement : `python3 -m solfege check`).
- Développer : `uv venv && uv pip install -e ".[dev]"`, puis `ruff check . && ruff format --check . && pytest`. Détails techniques : [ia/SPEC.md](ia/SPEC.md) ; régénérer le code en une fois : [ia/PROMPT.md](ia/PROMPT.md) ; pistes en attente : [TODO.md](TODO.md).

## Installation (macOS)

| Outil | Pour | Installation |
|---|---|---|
| Python ≥ 3.11 | tout | `brew install uv` puis `uv venv && uv pip install -e ".[dev]"` |
| LilyPond | générer le PDF | `brew install lilypond` ; ou `LILYPOND=/chemin/lilypond` |
| poppler (`pdftoppm`) | contrôle visuel seulement | `brew install poppler` |

Le code n'a aucune dépendance Python à l'exécution ; `pytest` et `ruff` servent au développement. La CI (GitHub Actions) installe LilyPond : elle vérifie aussi le rendu PDF, pas seulement le code et `cahier.txt`.
