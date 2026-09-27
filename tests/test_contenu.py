"""Le vrai cahier.txt respecte NOTATION.md et PEDAGOGIE.md (ce qui se vérifie)."""

import re
from pathlib import Path

import pytest

from solfege.cahier import load_cahier
from solfege.rythme import TOKENS, check

ROOT = Path(__file__).resolve().parent.parent
CAHIER = load_cahier(ROOT / "cahier.txt")
PEDAGOGIE = (ROOT / "PEDAGOGIE.md").read_text(encoding="utf-8")
LESSONS = list(CAHIER.lessons())
IDS = [f"{lesson.number} {lesson.title}" for _, lesson in LESSONS]


def symbols(lesson):
    return {s for ex in lesson.exercises for line in ex.lines for s in line.text.split() if s in TOKENS}


def test_aucune_erreur_de_rythme():
    assert check(CAHIER) == []


def test_progression_conforme_a_pedagogie():
    """« Progression actuelle » de PEDAGOGIE.md : nombre de pages et de leçons par chapitre."""
    pages = int(re.search(r"## Progression actuelle \(\d+ chapitres, (\d+) pages\)", PEDAGOGIE).group(1))
    chapters = re.findall(r"^\d+\. \*\*(.+?)\*\* : (.+)$", PEDAGOGIE, flags=re.MULTILINE)
    assert len(LESSONS) == pages
    assert [len(items.split(" · ")) for _, items in chapters] == [len(c.lessons) for c in CAHIER.chapters]
    assert [title for title, _ in chapters] == [c.title for c in CAHIER.chapters]


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


# Leçons qui introduisent une valeur ou un groupe : syllabes sous le 1er exercice (liste dans PEDAGOGIE.md)
DECOUVERTE = set(re.search(r"Leçons avec syllabes \(1er exercice\) : (.+)\.", PEDAGOGIE).group(1).split(", "))


@pytest.mark.parametrize(("chapter", "lesson"), LESSONS, ids=IDS)
def test_syllabes_pour_decouvrir(chapter, lesson):
    first = lesson.exercises[0].lines[0]
    if lesson.number in DECOUVERTE:
        assert first.syllables, "le 1er exercice d'une découverte montre les syllabes"


def test_liste_des_decouvertes_valide():
    numbers = {lesson.number for _, lesson in LESSONS}
    assert DECOUVERTE and numbers >= DECOUVERTE
