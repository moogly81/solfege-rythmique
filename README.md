# Cahier de solfège rythmique

Cahier de lecture rythmique (33 pages A4) pour une enfant de 6 ans : `cahier.txt` → MusicXML → PDF (MuseScore 4).

- Modifier le contenu : `cahier.txt`, format dans [NOTATION.md](NOTATION.md), règles dans [PEDAGOGIE.md](PEDAGOGIE.md).
- Générer : `python3 -m solfege` (vérifier seulement : `python3 -m solfege check`).
- Développer : `uv venv && uv pip install -e ".[dev]"`, puis `ruff check . && ruff format --check . && pytest`. Détails techniques : [ia/SPEC.md](ia/SPEC.md) ; régénérer le code en une fois : [ia/PROMPT.md](ia/PROMPT.md) ; pistes en attente : [TODO.md](TODO.md).

## Installation (macOS)

| Outil | Pour | Installation |
|---|---|---|
| Python ≥ 3.11 | tout | `brew install uv` puis `uv venv && uv pip install -e ".[dev]"` |
| MuseScore 4 (testé 4.7.x) | générer le PDF | [musescore.org](https://musescore.org) ; ou `MSCORE=/chemin/mscore` |
| qpdf | fusionner les pages | `brew install qpdf` ; ou `QPDF=/chemin/qpdf` |
| poppler (`pdftoppm`) | contrôle visuel seulement | `brew install poppler` |

Le code n'a aucune dépendance Python à l'exécution ; `pytest` et `ruff` servent au développement. La CI (GitHub Actions) n'a pas MuseScore : elle vérifie le code et `cahier.txt`, pas le PDF.
