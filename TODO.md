# À faire (décisions en attente)

Pistes issues des revues du 2026-09-27, non réalisées parce qu'elles demandent une nouvelle notation dans `cahier.txt` et du code, ou un changement d'outil. À trancher par l'auteur.

## Contenu (nouvelle notation + code + PEDAGOGIE/NOTATION)

- [ ] **Liaison** (note tenue par-dessus la barre de mesure) : symbole à inventer (par ex. `n~ | ~n`), `<tie>`/`<tied>` en MusicXML, leçon dans un chapitre « Les surprises » avant les révisions générales.
- [ ] **Levée / anacrouse** (exercice qui commence par une mesure incomplète) : mesure `implicit="yes"` en MusicXML, notation à définir (par ex. `- 4/4 : (n) | n n b …`).
- [ ] **Point d'orgue** : symbole (par ex. `n^`), `<fermata/>` en MusicXML.
- [ ] **Tempo indicatif** sur les pages de découverte (« Lentement », ♩ = 60) : nouvelle ligne `Tempo :` dans la leçon, `<direction><metronome>` ou texte.
- [ ] **Syllabes « 1 et 2 et »** : aucune leçon ne les affiche sous les notes (la consigne 4.1 les demande) ; décider si le tableau « Comptage » doit les inclure.

## Progression (`cahier.txt` + PEDAGOGIE, sans code)

- [ ] **Complexité croissante dans chaque leçon** (surtout à partir des chapitres 3 et 4) : aujourd'hui les exercices d'une leçon se ressemblent souvent. Ils devraient aller du plus simple au plus difficile (nouvelle valeur isolée, puis mélangée, puis enchaînements plus denses). Comme la difficulté monte, il faut aussi **assez d'exercices** pour assimiler chaque notion : plus de leçons (par ex. découverte + entraînement), ou plus d'exercices par leçon (mais la règle actuelle est 4 à 6 exercices sur une page A4). Mettre à jour PEDAGOGIE.md (règles et « Progression actuelle ») en même temps.

## Outil

- [x] **MuseScore → LilyPond** : fait sur la branche `outil/lilypond` (`solfege/lilypond.py` remplace `musicxml.py`, `rendu.py` appelle `lilypond` au lieu de `mscore`). CI installe LilyPond via `apt-get` et exécute désormais les tests `rendu` (avant ignorés, faute de MuseScore). Rendu vérifié visuellement (33 pages du vrai `cahier.txt`, `pdftoppm`) après correction du piton des notes (`c'`, centré sur la ligne), des syllabes numériques et de l'affichage des numéros de mesure.
- [ ] **Un seul fichier LilyPond pour tout le cahier** (`\pageBreak` par leçon, dans un seul `\book`) au lieu de 33 fichiers `.ly` + fusion `qpdf` : à essayer maintenant que le rendu passe par LilyPond (l'ancien blocage MuseScore sur les `<credit page="N">` au-delà de la page 1 ne s'applique plus).
- [ ] **Générer les artefacts** : publier `cahier_rythme.pdf` comme artefact de build CI (`actions/upload-artifact`) plutôt que (ou en plus de) le garder versionné dans le dépôt.
