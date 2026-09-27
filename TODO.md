# À faire (décisions en attente)

Pistes issues des revues du 2026-09-27, non réalisées parce qu'elles demandent une nouvelle notation dans `cahier.txt` et du code, ou un changement d'outil. À trancher par l'auteur.

## Contenu (nouvelle notation + code + PEDAGOGIE/NOTATION)

- [ ] **Liaison** (note tenue par-dessus la barre de mesure) : symbole à inventer (par ex. `n~ | ~n`), `<tie>`/`<tied>` en MusicXML, leçon dans un chapitre « Les surprises » avant les révisions générales.
- [ ] **Levée / anacrouse** (exercice qui commence par une mesure incomplète) : mesure `implicit="yes"` en MusicXML, notation à définir (par ex. `- 4/4 : (n) | n n b …`).
- [ ] **Point d'orgue** : symbole (par ex. `n^`), `<fermata/>` en MusicXML.
- [ ] **Tempo indicatif** sur les pages de découverte (« Lentement », ♩ = 60) : nouvelle ligne `Tempo :` dans la leçon, `<direction><metronome>` ou texte.
- [ ] **Syllabes « 1 et 2 et »** : aucune leçon ne les affiche sous les notes (la consigne 4.1 les demande) ; décider si le tableau « Comptage » doit les inclure.

## Outil

- [x] **MuseScore → LilyPond** : fait sur la branche `outil/lilypond` (`solfege/lilypond.py` remplace `musicxml.py`, `rendu.py` appelle `lilypond` au lieu de `mscore`). CI installe LilyPond via `apt-get` et exécute désormais les tests `rendu` (avant ignorés, faute de MuseScore). Rendu vérifié visuellement (33 pages du vrai `cahier.txt`, `pdftoppm`) après correction du piton des notes (`b`, pas `c`), des syllabes numériques et de l'affichage des numéros de mesure.
- [ ] **Un seul fichier LilyPond pour tout le cahier** (`\pageBreak` par leçon, dans un seul `\book`) au lieu de 33 fichiers `.ly` + fusion `qpdf` : à essayer maintenant que le rendu passe par LilyPond (l'ancien blocage MuseScore sur les `<credit page="N">` au-delà de la page 1 ne s'applique plus).
- [ ] **Générer les artefacts** : publier `cahier_rythme.pdf` comme artefact de build CI (`actions/upload-artifact`) plutôt que (ou en plus de) le garder versionné dans le dépôt.
