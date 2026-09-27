# Cahier de solfège rythmique : instructions pour l'agent

Sources de vérité (priorité décroissante en cas de conflit) :

1. @PEDAGOGIE.md : règles pédagogiques (public, progression, contenu à couvrir) ;
2. @NOTATION.md : format de `cahier.txt` (symboles, structure, limites de mise en page) ;
3. @ia/SPEC.md : toute la technique (architecture, choix MusicXML/MuseScore, tests, CI, critères d'acceptation).

`cahier.txt` = le contenu. Le code (`solfege/`, `tests/`, config) est **régénérable** depuis ces fichiers : voir `ia/PROMPT.md`.

## Règles de travail

- Ajouter ou modifier des exercices : éditer `cahier.txt`, **jamais le code**, en respectant PEDAGOGIE.md et NOTATION.md.
- Règle pédagogique modifiée : mettre à jour PEDAGOGIE.md. `tests/test_contenu.py` lit sa « Progression actuelle » (pages, titres de chapitres, leçons par chapitre) et « Leçons avec syllabes » : les garder alignées sur `cahier.txt`.
- Décision technique durable (rendu, contournement MuseScore, validation) : la reporter dans `ia/SPEC.md`, avec un test.
- Messages d'erreur lus par un non-technicien : français accentué, fichier + ligne + exercice + mesure.

## Vérifier après chaque modification

- `ruff check . && ruff format --check . && pytest`.
- `python3 -m solfege` : chaque `build/page_NN.pdf` fait 1 page (`qpdf --show-npages`). Sinon la leçon déborde : raccourcir des lignes.
- Rendu visuel : `pdftoppm -png -r 50 -f N -l N cahier_rythme.pdf "$TMPDIR/x"`, puis regarder l'image.
- Refactor sans changement de contenu : `build/page_*.musicxml` identiques octet pour octet (`cmp` contre une copie faite avant).
- Sandbox Claude Code : erreurs parasites de MuseScore (crashpad, XPC, DNS), sans lien. Le SIGABRT à la fermeture est connu (SPEC § 3.4).

## Environnement / git

- Dépôt **privé** GitHub `moogly81/solfege-rythmique`. Identité git **locale** au dépôt : moogly81, `2691085+moogly81@users.noreply.github.com`.
- Ne jamais modifier la config git globale : elle est pro (dsonney@pictet.com).
- `GH_TOKEN` pointe sur le compte pro (dsonney_pictet). Pour moogly81 : `env -u GH_TOKEN gh auth token --user moogly81`. Ne jamais afficher un token.
- Sandbox : écriture dans `.git` interdite. Donner à l'utilisateur la commande git à lancer avec `!`.
- Ne pas supprimer `.venv/` ni les PNG de `build/` sans demande explicite.
