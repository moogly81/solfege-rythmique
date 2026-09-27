# Régénérer l'application en une fois

## Fichiers d'entrée (à garder)

| Fichier | Contenu | Qui le modifie |
|---|---|---|
| `PEDAGOGIE.md` | règles pédagogiques, progression | l'auteur |
| `NOTATION.md` | format de `cahier.txt`, messages d'erreur | l'auteur |
| `cahier.txt` | le contenu musical | l'auteur |
| `ia/SPEC.md` | architecture, choix MusicXML/MuseScore, tests, CI, critères d'acceptation | l'agent / le développeur |
| `CLAUDE.md` | règles de travail de l'agent (environnement, git) | le développeur |

Tout le reste (`solfege/`, `tests/`, `pyproject.toml`, `.github/`, `README.md`, `solfege_rythmique.py`, `.gitignore`) est **généré**, et peut être supprimé puis recréé.

## Prompt à donner à Claude Code (à la racine du dépôt)

```
Lis ia/SPEC.md, PEDAGOGIE.md, NOTATION.md et cahier.txt.
Génère toute l'application décrite dans ia/SPEC.md : paquet solfege/, tests/,
pyproject.toml, .github/ (CI + Dependabot), .gitignore, README.md, solfege_rythmique.py.
Ne modifie ni PEDAGOGIE.md, ni NOTATION.md, ni cahier.txt.
Épingle pytest et ruff à leur dernière version (vérifie avec Context7 ou PyPI), idem
pour les actions GitHub.
Puis déroule les critères d'acceptation de ia/SPEC.md § 6 (tests, 1 page A4 par
leçon, contrôle visuel des pages indiquées) et corrige jusqu'à ce qu'ils passent.
Termine par un rapport : fichiers créés, résultats des tests, pages vérifiées.
```

Variante « nouveau contenu » : remplacer `cahier.txt` (ou demander à Claude de l'écrire d'après `PEDAGOGIE.md`) avant de lancer le prompt. `tests/test_contenu.py` vérifiera alors les règles de `PEDAGOGIE.md` sur le nouveau contenu.

## Après une évolution

Toute décision technique durable (nouveau choix de rendu, contournement d'un bug MuseScore, nouvelle règle de validation) doit être ajoutée à `ia/SPEC.md`. Sinon, elle sera perdue à la prochaine régénération.
