# Régénérer l'application en une fois

## Fichiers d'entrée (à garder)

| Fichier | Contenu | Qui le modifie |
|---|---|---|
| `PEDAGOGIE.md` | règles pédagogiques, progression | l'auteur |
| `NOTATION.md` | format de `cahier.txt`, messages d'erreur | l'auteur |
| `cahier.txt` | le contenu musical | l'auteur |
| `ia/SPEC.md` | architecture, choix MusicXML/MuseScore, tests, CI, critères d'acceptation | l'agent / le développeur |
| `CLAUDE.md` | règles de travail de l'agent (environnement, git) | le développeur |

| `tests/golden/exemple.txt` + `exemple_NN.musicxml` | référence binaire du rendu MusicXML | l'agent, seulement si le rendu change volontairement |

Tout le reste (`solfege/`, `tests/*.py`, `pyproject.toml`, `.github/`, `README.md`, `solfege_rythmique.py`, `.gitignore`) est **généré**, et peut être supprimé puis recréé. `cahier_rythme.pdf` est versionné : ne le régénérer qu'à la fin, quand tout passe.

## Prompt à donner à Claude Code (à la racine du dépôt)

```
Lis ia/SPEC.md, PEDAGOGIE.md, NOTATION.md et cahier.txt.
Génère toute l'application décrite dans ia/SPEC.md : paquet solfege/, tests/,
pyproject.toml, .github/ (CI + Dependabot), .gitignore, README.md, solfege_rythmique.py.
Ne modifie ni PEDAGOGIE.md, ni NOTATION.md, ni cahier.txt.
Épingle pytest et ruff à leur dernière version (vérifie avec Context7 ou PyPI), idem
pour les actions GitHub.
Ne touche pas à tests/golden/ : le MusicXML que tu produis doit lui être identique
octet pour octet (tests/test_golden.py), c'est la preuve que le rendu est le même.
Puis déroule les critères d'acceptation de ia/SPEC.md § 6 (tests, 1 page A4 par
leçon, contrôle visuel des pages indiquées avec pdftoppm) et corrige jusqu'à ce
qu'ils passent. La CI n'a pas MuseScore : le PDF se vérifie en local.
Termine par un rapport : fichiers créés, résultats des tests, pages vérifiées.
```

Prérequis sur la machine : MuseScore 4.7.x, `qpdf`, `pdftoppm` (poppler), un `.venv/` avec `pytest` et `ruff` (voir README.md, « Installation »).

Variante « nouveau contenu » : remplacer `cahier.txt` (ou demander à Claude de l'écrire d'après `PEDAGOGIE.md`) avant de lancer le prompt. `tests/test_contenu.py` vérifiera alors les règles de `PEDAGOGIE.md` sur le nouveau contenu.

## Après une évolution

Toute décision technique durable (nouveau choix de rendu, contournement d'un bug MuseScore, nouvelle règle de validation) doit être ajoutée à `ia/SPEC.md`. Sinon, elle sera perdue à la prochaine régénération.
