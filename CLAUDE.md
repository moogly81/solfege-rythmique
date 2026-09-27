# Cahier de solfège rythmique

Support PDF de lecture rythmique pour une enfant de 6 ans qui débute. Auteur : musicien (tromboniste).

## Pipeline

`solfege_rythmique.py` : `PAGES` (données) → un MusicXML par page (`build/`) → PDF via MuseScore 4 CLI (`-j` job + `-S` style) → fusion avec `qpdf` → `cahier_rythme.pdf`.

- Lancer : `python3 solfege_rythmique.py` (pas de dépendance Python externe).
- Prérequis : MuseScore 4 (`/Applications/MuseScore 4.app`), `qpdf`. Surcharge : env `MSCORE`, `QPDF`.
- Vérifier le rendu : `pdftoppm -png -r 60 -f N -l N cahier_rythme.pdf out` puis regarder l'image. Chaque `build/page_NN.pdf` doit faire exactement 1 page (`qpdf --show-npages`).

## Contraintes musicales

- 4/4 uniquement. Ligne rythmique à 1 ligne (pas de portée 5 lignes, pas de hauteur).
- Afficher clé de percussion + chiffrage 4/4 en début de page.
- Croches/doubles-croches ligaturées par temps (automatique, `compute_beams`).
- Barres de mesure entre chaque mesure, double barre finale.
- Silences obligatoires dans la progression : pause, demi-pause, soupir, demi-soupir. Utiliser les glyphes MuseScore (pas de dessin maison).

## Contraintes pédagogiques

- Enfant de 6 ans : mise en page aérée, grosses notes, titre + consigne courte par page (« Compte 1 et 2 et… »).
- 6 à 10 lignes par page, une page = une feuille A4.
- **Jamais une page entière d'une seule valeur.** Une page qui introduit une valeur : 1 ligne de découverte, puis mélange avec les valeurs déjà connues.
- Chaque nouvelle valeur (note ou silence) a sa page d'introduction, puis des pages de révision.
- Progression actuelle (16 pages) : ronde+pause → blanche → demi-pause → révision → noire → soupir → révision → croche → croches+tout → demi-soupir → croches+silences → double-croche → doubles+croches → doubles+silences → révision générale ×2.

## Format du contenu

`PAGES` = liste de dicts `{title, instruction, lines}`. Chaque ligne = chaîne, mesures séparées par `|`, codes : `r` ronde, `b` blanche, `n` noire, `c` croche, `d` double, `p` pause, `dp` demi-pause, `s` soupir, `ds` demi-soupir. Chaque mesure = 4 temps (vérifié au lancement).

- Lignes denses (croches/doubles partout) : max 3 mesures par ligne, sinon MuseScore déborde sur une 2e page.
- Taille/espacement : `STAFF_SIZE_MM`, `STYLE_MSS` (réglages MuseScore 4).

## Problème connu : MuseScore plante à la fermeture

MuseScore 4.7.5 fait un SIGABRT (`mutex lock failed`) dans `exit()` pendant la destruction des statiques, **après** avoir écrit les PDF (pile : `exit → __cxa_finalize → mscore → std::terminate`). Bug interne MuseScore, non corrigible de notre côté. Le script juge le succès sur la présence des PDF, pas sur le code retour ; sortie dans `build/mscore.log`. Le sandbox Claude Code ajoute des erreurs parasites (crashpad, XPC, DNS) sans lien.
