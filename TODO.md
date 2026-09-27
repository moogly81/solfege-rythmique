# À faire (décisions en attente)

Pistes issues des revues du 2026-09-27, non réalisées parce qu'elles demandent une nouvelle notation dans `cahier.txt` et du code, ou un changement d'outil. À trancher par l'auteur.

## Contenu (nouvelle notation + code + PEDAGOGIE/NOTATION)

- [ ] **Liaison** (note tenue par-dessus la barre de mesure) : symbole à inventer (par ex. `n~ | ~n`), `<tie>`/`<tied>` en MusicXML, leçon dans un chapitre « Les surprises » avant les révisions générales.
- [ ] **Levée / anacrouse** (exercice qui commence par une mesure incomplète) : mesure `implicit="yes"` en MusicXML, notation à définir (par ex. `- 4/4 : (n) | n n b …`).
- [ ] **Point d'orgue** : symbole (par ex. `n^`), `<fermata/>` en MusicXML.
- [ ] **Tempo indicatif** sur les pages de découverte (« Lentement », ♩ = 60) : nouvelle ligne `Tempo :` dans la leçon, `<direction><metronome>` ou texte.
- [ ] **Syllabes « 1 et 2 et »** : aucune leçon ne les affiche sous les notes (la consigne 4.1 les demande) ; décider si le tableau « Comptage » doit les inclure.

## Outil

- [ ] **MuseScore → LilyPond** : LilyPond (`brew install lilypond`, disponible sur les runners CI) donnerait un rendu déterministe et testable en CI, sans le SIGABRT à la fermeture ni la dépendance à une application graphique. Coût : réécrire `musicxml.py` en générateur `.ly` et revalider tout le rendu (ligatures, triolets, syllabes, une ligne, 1 page par leçon).
- [ ] **Un seul MusicXML pour tout le cahier** (`<print new-page="yes"/>` par leçon) au lieu de 33 fichiers + `job.json` + fusion `qpdf` : à essayer, MuseScore importe mal les `<credit page="N">` au-delà de la page 1.
- [ ] **Générer les artefacts** : publier `cahier_rythme.pdf` comme artefact de build CI (`actions/upload-artifact`) plutôt que (ou en plus de) le garder versionné dans le dépôt.
