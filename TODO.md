# À faire (décisions en attente)

Pistes issues des revues du 2026-09-27, non réalisées parce qu'elles demandent une nouvelle notation dans `cahier.txt` et du code, ou un changement d'outil. À trancher par l'auteur.

## Contenu (nouvelle notation + code + PEDAGOGIE/NOTATION)

- [ ] **Liaison** (note tenue par-dessus la barre de mesure) : symbole à inventer (par ex. `n~ | ~n`), `~` en LilyPond, leçon dans un chapitre « Les surprises » avant les révisions générales.
- [ ] **Levée / anacrouse** (exercice qui commence par une mesure incomplète) : `\partial` en LilyPond (et le compte des temps de `parse_line` à adapter), notation à définir (par ex. `- 4/4 : (n) | n n b …`).
- [ ] **Point d'orgue** : symbole (par ex. `n^`), `\fermata` en LilyPond.
- [ ] **Tempo indicatif** sur les pages de découverte (« Lentement », ♩ = 60) : nouvelle ligne `Tempo :` dans la leçon, `\tempo "Lentement" 4 = 60` en LilyPond.
- [ ] **Syllabes « 1 et 2 et »** : aucune leçon ne les affiche sous les notes (la consigne 4.1 les demande) ; décider si le tableau « Comptage » doit les inclure.

## Progression (`cahier.txt` + PEDAGOGIE, sans code)

- [x] **Complexité croissante dans chaque leçon** (surtout à partir des chapitres 3 et 4) : aujourd'hui les exercices d'une leçon se ressemblent souvent. Ils devraient aller du plus simple au plus difficile (nouvelle valeur isolée, puis mélangée, puis enchaînements plus denses). Comme la difficulté monte, il faut aussi **assez d'exercices** pour assimiler chaque notion : plus de leçons (par ex. découverte + entraînement), ou plus d'exercices par leçon (mais la règle actuelle est 4 à 6 exercices sur une page A4). Mettre à jour PEDAGOGIE.md (règles et « Progression actuelle ») en même temps. Fait : exercices réordonnés du simple au dense, une leçon d'entraînement après contretemps, syncope et croche pointée + double (36 pages), règle dans PEDAGOGIE.md, vérifiée par `test_complexite_croissante`.

## Outil

- [x] **MuseScore → LilyPond** : fait sur la branche `outil/lilypond` (`solfege/lilypond.py` remplace `musicxml.py`, `rendu.py` appelle `lilypond` au lieu de `mscore`). CI installe LilyPond via `apt-get` et exécute désormais les tests `rendu` (avant ignorés, faute de MuseScore). Rendu vérifié visuellement (33 pages du vrai `cahier.txt`, `pdftoppm`) après correction du piton des notes (`c'`, centré sur la ligne), des syllabes numériques et de l'affichage des numéros de mesure.
- [x] **Un seul fichier LilyPond pour tout le cahier** : `build/cahier.ly`, un `\bookpart` par leçon, au lieu de 33 fichiers `.ly` + fusion `qpdf` (qpdf n'est plus nécessaire). Débordements détectés par `page-post-process` (nombre de pages de chaque leçon dans `build/lilypond.log`). Rendu identique au pixel près (33 pages, `pdftoppm -r 50`).
- [x] **Générer les artefacts** : publier `cahier_rythme.pdf` comme artefact de build CI (`actions/upload-artifact`) plutôt que (ou en plus de) le garder versionné dans le dépôt. Fait : artefact `cahier_rythme` (PDF + `build/lilypond.log`) à chaque exécution de la CI (job Python 3.x) ; le PDF reste aussi versionné. Release GitHub avec le PDF à chaque tag `v*` (`release.yml`).
