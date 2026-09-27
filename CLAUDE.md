# Cahier de solfège rythmique : instructions techniques

Ce fichier ne contient **que la technique**. Le reste vit dans trois fichiers modifiables par un non-technicien, qui priment en cas de conflit :

- @PEDAGOGIE.md : règles pédagogiques (public, progression, contenu à couvrir) ;
- @NOTATION.md : format de `cahier.txt` (symboles, structure, limites de mise en page) ;
- `cahier.txt` : le contenu (chapitres, leçons, consignes, exercices).

Pour ajouter ou modifier des exercices, **éditer `cahier.txt`, jamais le script**, en respectant PEDAGOGIE.md et NOTATION.md. Si une règle pédagogique change, mettre à jour PEDAGOGIE.md (et la « Progression actuelle » quand des leçons sont ajoutées ou retirées).

## Pipeline

`cahier.txt` → `load_cahier()` → un MusicXML par page (`build/`) → PDF via MuseScore 4 CLI (`-j` job + `-S` style) → fusion avec `qpdf` → `cahier_rythme.pdf`.

- Lancer : `python3 solfege_rythmique.py` (pas de dépendance Python externe ; `.venv/` = reste de l'ancienne version reportlab).
- Prérequis : MuseScore 4 (`/Applications/MuseScore 4.app`), `qpdf`. Surcharge : env `MSCORE`, `QPDF`.
- Sections du script :
  1. lecture de `cahier.txt` ;
  2. réglages de mise en page (`STAFF_SIZE_MM`, `STYLE_MSS`) ;
  3. valeurs (`TOKENS`, 12 divisions par noire) et validation (`parse_line`) ;
  4. ligatures (`compute_beams`) ;
  5. MusicXML ;
  6. rendu et fusion.

## Vérifier après chaque modification

- Chaque `build/page_NN.pdf` fait exactement 1 page (`qpdf --show-npages`). Sinon, la leçon déborde : raccourcir des lignes.
- Rendu visuel : `pdftoppm -png -r 50 -f N -l N cahier_rythme.pdf "$TMPDIR/x"`, puis regarder l'image.
- Pour un refactor sans changement de contenu : les `build/page_*.musicxml` doivent rester identiques octet pour octet (`cmp` contre une copie faite avant).
- Les messages d'erreur sont lus par un non-technicien : français accentué, fichier + numéro de ligne + exercice + mesure.

## Choix de rendu (MusicXML / MuseScore)

- Portée de percussion à 1 ligne : `staff-lines` 1, clé `percussion`, instrument non accordé (`score-instrument` Hand Clap, `midi-unpitched`), `<instrument>` dans chaque note. Sans instrument, MuseScore importe une portée de piano et place les notes sous la ligne.
- Chaque exercice :
  - nouvelle ligne (`print new-system`) ;
  - chiffrage réémis ;
  - repère `rehearsal` encadré N.M.K ;
  - double barre `light-heavy`.
- Pas de chiffrage de courtoisie (`genCourtesyTimesig` 0). Numéros de mesure masqués via le style `-S` : `<print><measure-numbering>` est ignoré.
- En-tête = **un seul** credit `title` à 3 `credit-words` (chapitre / titre / consigne). Plusieurs credits distincts se chevauchent.
- Triolets : `time-modification` 3:2 plus `tuplet bracket="no"` (le 3 s'affiche sur la ligature). Pause `p` = `rest measure="yes"`, durée de la mesure.
- Silences : toujours les glyphes MuseScore, jamais de dessin maison.

## Problème connu : MuseScore plante à la fermeture

MuseScore 4.7.5 fait un SIGABRT (`mutex lock failed`) dans `exit()` pendant la destruction des statiques, **après** avoir écrit les PDF (pile : `exit → __cxa_finalize → mscore → std::terminate`). C'est un bug interne à MuseScore, non corrigible de notre côté. Le script juge le succès sur la présence des PDF, pas sur le code retour ; la sortie va dans `build/mscore.log`. Le sandbox Claude Code ajoute des erreurs parasites (crashpad, XPC, DNS) sans lien.

## Environnement / git

- Dépôt **privé** GitHub `moogly81/solfege-rythmique`. Identité git **locale** au dépôt : moogly81, `2691085+moogly81@users.noreply.github.com`.
- Ne jamais modifier la config git globale : elle est pro (dsonney@pictet.com).
- `GH_TOKEN` pointe sur le compte pro (dsonney_pictet). Pour moogly81 : `env -u GH_TOKEN gh auth token --user moogly81`. Ne jamais afficher un token.
- Sandbox : écriture dans `.git` interdite. Donner à l'utilisateur la commande git à lancer avec `!`.
- Ne pas supprimer `.venv/` ni les PNG de `build/` sans demande explicite.
