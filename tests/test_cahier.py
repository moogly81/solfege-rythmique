import pytest

from solfege.cahier import parse_cahier
from solfege.erreurs import CahierError

EXEMPLE = """\
// commentaire
# Chapitre 7 : Le temps

## La noire
Consigne : Compte 1 - 2 - 3 - 4.
Mesure : 3/4

- n n n | b n
- 4/4 : r | n n b
  b b | p

## Révision
- n n n n
"""


def test_structure_et_numerotation():
    cahier = parse_cahier(EXEMPLE)
    (chapter,) = cahier.chapters
    assert (chapter.number, chapter.title) == (1, "Le temps")  # numéro écrit ignoré
    noire, revision = chapter.lessons
    assert (noire.number, noire.title, noire.instruction, noire.time) == (
        "1.1",
        "La noire",
        "Compte 1 - 2 - 3 - 4.",
        "3/4",
    )
    assert [ex.number for ex in noire.exercises] == ["1.1.1", "1.1.2"]
    assert revision.time == "4/4"  # chiffrage par défaut


def test_exercice_chiffrage_propre_et_deux_lignes():
    ex1, ex2 = parse_cahier(EXEMPLE).chapters[0].lessons[0].exercises
    assert ex1.time == "3/4"
    assert ex2.time == "4/4"
    assert [line.text for line in ex2.lines] == ["r | n n b", "b b | p"]
    assert ex2.where == "cahier.txt, ligne 9 (exercice 1.1.2)"
    assert ex2.lines[1].where == "cahier.txt, ligne 10"


def test_titre_sans_prefixe_chapitre():
    cahier = parse_cahier("# Bonus\n## L\n- r\n")
    assert cahier.chapters[0].title == "Bonus"


@pytest.mark.parametrize(
    ("texte", "message"),
    [
        ("", "cahier.txt : aucun chapitre trouvé"),
        ("## L\n- r\n", "ligne 1 : une leçon (##) doit être dans un chapitre"),
        ("# C\n- r\n", "ligne 2 : texte hors d'une leçon : « - r »"),
        ("# C\n## L\nr | r\n", "ligne 3 : ligne non comprise : « r | r »"),
        ("# C\n## Vide\n", "ligne 2 : la leçon « Vide » n'a aucun exercice"),
        ("# C\n## L\n- r\n  r\n  r\n", "ligne 3 (exercice 1.1.1) : un exercice fait 1 ou 2 lignes, pas 3"),
    ],
)
def test_erreurs_de_structure(texte, message):
    with pytest.raises(CahierError, match=message.replace("(", r"\(").replace(")", r"\)")):
        parse_cahier(texte)


def test_source_dans_les_messages():
    with pytest.raises(CahierError, match=r"^mon.txt, ligne 1 :"):
        parse_cahier("n n\n", source="mon.txt")


def test_ligne_de_syllabes():
    cahier = parse_cahier("# C\n## L\n- d d d d n b\n  = qua- tre dou- bles 2 3\n  r\n")
    first, second = cahier.chapters[0].lessons[0].exercises[0].lines
    assert first.syllables == "qua- tre dou- bles 2 3"
    assert first.syllables_where == "cahier.txt, ligne 4"
    assert second.syllables is None  # ne compte pas comme une 3e ligne


def test_deux_lignes_de_syllabes_refusees():
    with pytest.raises(CahierError, match="ligne 5 : une seule ligne de syllabes"):
        parse_cahier("# C\n## L\n- r\n  = 1\n  = 1\n")
