import xml.etree.ElementTree as ET

import pytest

from solfege.cahier import parse_cahier
from solfege.erreurs import CahierError
from solfege.musicxml import lesson_to_musicxml

CAHIER = """\
# Chapitre 1 : Tout <mélangé> & co
## Essai
Consigne : Regarde le chiffrage !
Mesure : 3/4
- b. | p | t t t n n
  n. c n
- 2/4 : c. d c d d | d d c n
"""


@pytest.fixture
def root():
    cahier = parse_cahier(CAHIER)
    chapter = cahier.chapters[0]
    return ET.fromstring(lesson_to_musicxml(chapter, chapter.lessons[0]).encode())


def test_mesures_et_nouvelles_lignes(root):
    measures = root.findall("part/measure")
    assert [m.get("number") for m in measures] == [str(i) for i in range(1, 7)]
    new_system = [m.get("number") for m in measures if m.find("print[@new-system='yes']") is not None]
    assert new_system == ["4", "5"]  # 2e ligne de l'exercice 1, puis exercice 2


def test_reperes_et_chiffrages(root):
    assert [r.text for r in root.iter("rehearsal")] == ["1.1.1", "1.1.2"]
    assert [t.findtext("beats") for t in root.iter("time")] == ["3", "2"]


def test_double_barre_en_fin_d_exercice(root):
    ends = [m.get("number") for m in root.findall("part/measure") if m.findtext("barline/bar-style") == "light-heavy"]
    assert ends == ["4", "6"]


def test_pause_de_mesure_et_points(root):
    m2 = root.findall("part/measure")[1]
    (note,) = m2.findall("note")
    assert note.find("rest").get("measure") == "yes"
    assert note.findtext("duration") == "36"
    assert len(root.findall(".//note/dot")) == 3  # b. n. c.


def test_triolet(root):
    m3 = root.findall("part/measure")[2]
    tuplets = [n.find("notations/tuplet") for n in m3.findall("note")[:3]]
    assert [t.get("type") if t is not None else None for t in tuplets] == ["start", None, "stop"]
    assert all(n.findtext("time-modification/actual-notes") == "3" for n in m3.findall("note")[:3])


def test_en_tete_echappe(root):
    words = [w.text for w in root.iter("credit-words")]
    assert words == ["Chapitre 1 · Tout <mélangé> & co\n", "1.1  Essai\n", "Regarde le chiffrage !"]


def test_rythme_faux_refuse():
    cahier = parse_cahier("# C\n## L\n- n n n\n")
    chapter = cahier.chapters[0]
    with pytest.raises(CahierError, match="3 temps au lieu de 4"):
        lesson_to_musicxml(chapter, chapter.lessons[0])
