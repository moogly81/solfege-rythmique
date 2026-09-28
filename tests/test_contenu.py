"""Le vrai cahier.txt respecte NOTATION.md et PEDAGOGIE.md (ce qui se vérifie).

PEDAGOGIE.md est lu tel quel ; les lignes attendues (grammaire exacte, voir ia/SPEC.md § 4) :
  ## Progression actuelle (N chapitres, M pages)
  N. **Titre du chapitre** : leçon 1 · leçon 2 · leçon 3
  Leçons avec syllabes (1er exercice) : 1.1, 1.2, 2.1.
"""

import re

import pytest

from solfege.cahier import load_cahier
from solfege.rythme import TOKENS, check, parse_exercise

from .conftest import CAHIER_PATH, PEDAGOGIE_PATH

CAHIER = load_cahier(CAHIER_PATH)
PEDAGOGIE = PEDAGOGIE_PATH.read_text(encoding="utf-8")
LESSONS = list(CAHIER.lessons())
IDS = [f"{lesson.number} {lesson.title}" for _, lesson in LESSONS]


def _pedagogie(pattern: str, what: str) -> re.Match:
    match = re.search(pattern, PEDAGOGIE, flags=re.MULTILINE)
    assert match, f"PEDAGOGIE.md : ligne « {what} » introuvable ou mal formée (motif : {pattern})"
    return match


def symbols(lesson):
    return {s for ex in lesson.exercises for line in ex.lines for s in line.text.split() if s in TOKENS}


def test_aucune_erreur_de_rythme():
    assert check(CAHIER) == []


def test_progression_conforme_a_pedagogie():
    """« Progression actuelle » de PEDAGOGIE.md : nombre de pages et de leçons par chapitre."""
    header = _pedagogie(r"^## Progression actuelle \((\d+) chapitres, (\d+) pages\)$", "## Progression actuelle (…)")
    n_chapters, pages = int(header.group(1)), int(header.group(2))
    chapters = re.findall(r"^\d+\. \*\*(.+?)\*\* : (.+)$", PEDAGOGIE, flags=re.MULTILINE)
    assert len(chapters) == n_chapters, "une ligne « N. **Titre** : a · b » par chapitre"
    assert len(LESSONS) == pages
    assert [title for title, _ in chapters] == [c.title for c in CAHIER.chapters]
    assert [len(items.split(" · ")) for _, items in chapters] == [len(c.lessons) for c in CAHIER.chapters]


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_taille_de_la_lecon(chapter, lesson):
    n_lines = sum(len(ex.lines) for ex in lesson.exercises)
    assert 4 <= len(lesson.exercises) <= 6, "4 à 6 exercices par leçon"
    assert 6 <= n_lines <= 10, "6 à 10 lignes de musique par leçon"


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_consigne_presente(chapter, lesson):
    # la largeur (titre, consigne) est vérifiée par check(), donc par test_aucune_erreur_de_rythme
    assert lesson.instruction


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_jamais_une_seule_valeur(chapter, lesson):
    # 1.1 n'a que la ronde comme note : la pause compte comme 2e valeur
    assert len(symbols(lesson)) >= 2, f"une seule valeur : {symbols(lesson)}"


def signes_par_temps(exercise) -> float:
    """Densité de lecture : notes et silences (une pause compte pour 1) par temps."""
    beats, lines = parse_exercise(exercise)
    measures = [m for line in lines for m in line.measures]
    return sum(len(m) for m in measures) / (len(measures) * beats)


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_complexite_croissante(chapter, lesson):
    # du plus simple au plus difficile : le 2e exercice n'est pas plus chargé que le dernier
    second, last = lesson.exercises[1], lesson.exercises[-1]
    d_second, d_last = signes_par_temps(second), signes_par_temps(last)
    assert d_second <= d_last, (
        f"{second.number} ({d_second:.2f} signes par temps) plus chargé que {last.number} ({d_last:.2f})"
    )


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_pas_plus_de_huit_doubles_d_affilee(chapter, lesson):
    for ex in lesson.exercises:
        for line in ex.lines:
            run = 0
            for token in line.text.replace("|", " ").split():
                run = run + 1 if token == "d" else 0
                assert run <= 8, f"{ex.number} : {line.text}"


# Leçons qui introduisent une valeur ou un groupe : syllabes sous le 1er exercice (liste dans PEDAGOGIE.md)
DECOUVERTE = set(
    _pedagogie(r"^Leçons avec syllabes \(1er exercice\) : (.+)\.$", "Leçons avec syllabes (1er exercice) : …")
    .group(1)
    .split(", ")
)


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_syllabes_pour_decouvrir(chapter, lesson):
    first = lesson.exercises[0].lines[0]
    if lesson.number in DECOUVERTE:
        assert first.syllables, "le 1er exercice d'une découverte montre les syllabes"
    else:
        assert not first.syllables, "leçon avec syllabes absente de la liste de PEDAGOGIE.md"


def test_liste_des_decouvertes_valide():
    numbers = {lesson.number for _, lesson in LESSONS}
    assert DECOUVERTE and numbers >= DECOUVERTE
