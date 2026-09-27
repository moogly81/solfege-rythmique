# Cahier de solfège rythmique : instructions pour l'agent

Sources de vérité (priorité décroissante en cas de conflit) :

1. @PEDAGOGIE.md : règles pédagogiques (public, progression, contenu à couvrir) ;
2. @NOTATION.md : format de `cahier.txt` (symboles, structure, limites de mise en page) ;
3. @ia/SPEC.md : toute la technique (architecture, choix LilyPond, tests, CI, critères d'acceptation).

`cahier.txt` = le contenu. Le code (`solfege/`, `tests/`, config) est **régénérable** depuis ces fichiers : voir `ia/PROMPT.md`.

## Règles de travail

- Ajouter ou modifier des exercices : éditer `cahier.txt`, **jamais le code**, en respectant PEDAGOGIE.md et NOTATION.md.
- Règle pédagogique modifiée : mettre à jour PEDAGOGIE.md. `tests/test_contenu.py` lit sa « Progression actuelle » (pages, titres de chapitres, leçons par chapitre) et « Leçons avec syllabes » : les garder alignées sur `cahier.txt`.
- Décision technique durable (rendu, contournement LilyPond, validation) : la reporter dans `ia/SPEC.md`, avec un test.
- Messages d'erreur lus par un non-technicien : français accentué, fichier + ligne + exercice + mesure.

## Vérifier après chaque modification

- Outils : `.venv/bin/ruff`, `.venv/bin/pytest` (si absents : `uv venv && uv pip install -e ".[dev]"`, à faire lancer par l'utilisateur si le sandbox refuse) ; `qpdf`, `pdftoppm` (poppler), LilyPond (`brew install lilypond`).
- `ruff check . && ruff format --check . && pytest`.
- `python3 -m solfege` : code de retour 0 ; un code 2 signale sur stderr « la leçon N.M déborde » : raccourcir des lignes.
- Rendu visuel : `pdftoppm -png -r 50 -f N -l N cahier_rythme.pdf "$TMPDIR/x"`, puis regarder l'image (au moins les pages de « Leçons avec syllabes »).
- Refactor sans changement de rendu : `tests/test_golden.py` passe tel quel. Rendu changé volontairement : `pytest tests/test_golden.py --regenerer-golden`, et le dire.
- Sandbox Claude Code : LilyPond n'est pas installable dans le sandbox (Homebrew hors des répertoires autorisés en écriture) ; la CI GitHub (qui installe LilyPond via `apt-get`) et un contrôle local par l'utilisateur restent nécessaires pour valider le rendu réel.

## Environnement / git

- Dépôt **public** GitHub. Identités git/GitHub (compte perso vs pro, adresses, `GH_TOKEN`) : voir `.claude/identite.md` (non versionné, ne pas recréer ces infos ici).
- Ne jamais modifier la config git globale : elle est pro.
- Sandbox : écriture dans `.git` interdite. Donner à l'utilisateur la commande git à lancer avec `!`.
- Ne pas supprimer `.venv/` ni les PNG de `build/` sans demande explicite.
