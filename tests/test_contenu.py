"""Le vrai cahier.txt respecte NOTATION.md et PEDAGOGIE.md (ce qui se vérifie)."""

from pathlib import Path

import pytest

from solfege.cahier import load_cahier
from solfege.rythme import TOKENS, check

ROOT = Path(__file__).resolve().parent.parent
CAHIER = load_cahier(ROOT / "cahier.txt")
LESSONS = list(CAHIER.lessons())
IDS = [f"{lesson.number} {lesson.title}" for _, lesson in LESSONS]


def symbols(lesson):
    return {s for ex in lesson.exercises for line in ex.lines for s in line.text.split() if s in TOKENS}


def test_aucune_erreur_de_rythme():
    assert check(CAHIER) == []


def test_nombre_de_pages():
    assert len(LESSONS) == 25


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_taille_de_la_lecon(chapter, lesson):
    n_lines = sum(len(ex.lines) for ex in lesson.exercises)
    assert 4 <= len(lesson.exercises) <= 6, "4 à 6 exercices par leçon"
    assert 6 <= n_lines <= 10, "6 à 10 lignes de musique par leçon"


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_consigne_presente(chapter, lesson):
    assert lesson.instruction


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_jamais_une_seule_valeur(chapter, lesson):
    # 1.1 n'a que la ronde comme note : la pause compte comme 2e valeur
    assert len(symbols(lesson)) >= 2, f"une seule valeur : {symbols(lesson)}"
