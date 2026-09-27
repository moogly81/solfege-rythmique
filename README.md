# Cahier de solfège rythmique

Cahier de lecture rythmique (31 pages A4) pour une enfant de 6 ans : `cahier.txt` → MusicXML → PDF (MuseScore 4).

- Modifier le contenu : `cahier.txt`, format dans [NOTATION.md](NOTATION.md), règles dans [PEDAGOGIE.md](PEDAGOGIE.md).
- Générer : `python3 -m solfege` (vérifier seulement : `python3 -m solfege check`). Prérequis : MuseScore 4, `qpdf`.
- Développer : `pip install -e ".[dev]"`, puis `ruff check . && pytest`. Détails techniques : [ia/SPEC.md](ia/SPEC.md) ; régénérer le code en une fois : [ia/PROMPT.md](ia/PROMPT.md).
