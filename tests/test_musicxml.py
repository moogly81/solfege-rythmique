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


def xml_of(text: str) -> ET.Element:
    """MusicXML (bien formé) de la 1re leçon d'un cahier donné en texte."""
    chapter = parse_cahier(text).chapters[0]
    return ET.fromstring(lesson_to_musicxml(chapter, chapter.lessons[0]).encode())


@pytest.fixture
def root():
    return xml_of(CAHIER)


def test_mesures_et_nouvelles_lignes(root):
    measures = root.findall("part/measure")
    assert [m.get("number") for m in measures] == [str(i) for i in range(1, 7)]
    new_system = [m.get("number") for m in measures if m.find("print[@new-system='yes']") is not None]
    assert new_system == ["4", "5"]  # 2e ligne de l'exercice 1, puis exercice 2


def test_reperes_et_chiffrages(root):
    assert [r.text for r in root.iter("rehearsal")] == ["1.1.1", "1.1.2"]
    assert [r.get("enclosure") for r in root.iter("rehearsal")] == ["rectangle", "rectangle"]
    assert [t.findtext("beats") for t in root.iter("time")] == ["3", "2"]


def test_portee_de_rythme(root):
    """1 ligne, clé de percussion, armure masquée : une seule fois, sur la 1re mesure."""
    (attrs,) = root.findall("part/measure[@number='1']/attributes")
    assert attrs.findtext("staff-details/staff-lines") == "1"
    assert attrs.findtext("clef/sign") == "percussion"
    assert attrs.find("key").get("print-object") == "no"
    assert attrs.findtext("divisions") == "12"
    assert root.find("part/measure[@number='5']/attributes/clef") is None


def test_instrument_non_accorde_sur_chaque_note(root):
    """Sans instrument non accordé, MuseScore importe un piano et met les notes sous la ligne."""
    (score_part,) = root.findall("part-list/score-part")
    assert score_part.find("part-name").get("print-object") == "no"
    assert score_part.findtext("score-instrument/instrument-name") == "Hand Clap"
    assert score_part.findtext("midi-instrument/midi-unpitched") == "40"
    notes = [n for n in root.iter("note") if n.find("rest") is None]
    assert notes and all(n.find("instrument").get("id") == "P1-I1" for n in notes)
    assert all(n.findtext("unpitched/display-step") == "B" for n in notes)
    rests = [n for n in root.iter("note") if n.find("rest") is not None]
    assert rests and all(n.find("instrument") is None and n.find("unpitched") is None for n in rests)


def test_hampes_en_haut_sauf_ronde():
    root = xml_of("# C\n## L\n- r | b b | n c c ds c n\n")
    stems = [n.findtext("stem") for n in root.iter("note") if n.find("rest") is None]
    assert stems == [None, "up", "up", "up", "up", "up", "up", "up"]


def test_ordre_des_elements_de_note():
    """MusicXML impose l'ordre des enfants de <note> ; MuseScore refuse le fichier sinon."""
    order = ["rest", "unpitched", "duration", "instrument", "voice", "type", "dot", "time-modification", "stem"]
    order += ["beam", "notations", "lyric"]
    root = xml_of("# C\n## L\n- c. d t t t n. ds\n  = sau- te tri- o- let noir (ch)\n")
    for note in root.iter("note"):
        tags = [child.tag for child in note]
        assert tags == sorted(tags, key=order.index), tags


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
    assert tuplets[0].get("bracket") == "no"
    assert all(n.findtext("time-modification/actual-notes") == "3" for n in m3.findall("note")[:3])


def test_un_seul_credit_sur_trois_lignes(root):
    (credit,) = root.findall("credit")
    assert credit.findtext("credit-type") == "title"
    words = [w.text for w in credit.iter("credit-words")]
    assert words == ["Chapitre 1 · Tout <mélangé> & co\n", "1.1  Essai\n", "Regarde le chiffrage !"]
    assert [w.get("font-size") for w in credit.iter("credit-words")] == ["12", "22", "13"]
    assert root.findtext("work/work-title") == "1.1  Essai"


def test_mise_en_page_a4(root):
    assert root.findtext("defaults/scaling/millimeters") == "8.5"
    layout = root.find("defaults/page-layout")
    assert (layout.findtext("page-height"), layout.findtext("page-width")) == ("1398", "988")
    assert root.findtext("defaults/system-layout/top-system-distance") == "150"


def test_rythme_faux_refuse():
    cahier = parse_cahier("# C\n## L\n- n n n\n")
    chapter = cahier.chapters[0]
    with pytest.raises(CahierError, match="3 temps au lieu de 4"):
        lesson_to_musicxml(chapter, chapter.lessons[0])


def test_syllabes_sous_les_notes():
    root = xml_of("# C\n## L\n- d d d d s n n\n  = qua- tre dou- bles & 3\n")
    lyrics = [(n.findtext("lyric/syllabic"), n.findtext("lyric/text")) for n in root.iter("note")]
    assert lyrics == [
        ("begin", "qua"),
        ("end", "tre"),
        ("begin", "dou"),
        ("end", "bles"),
        (None, None),  # soupir : pas de syllabe
        ("single", "&"),
        ("single", "3"),
    ]


def test_syllabe_avec_espace():
    root = xml_of("# C\n## L\n- r\n  = ron-de_lon-gue\n")
    assert root.findtext(".//lyric/text") == "ron-de lon-gue"


def test_syllabe_chuchotee_sous_un_silence():
    root = xml_of("# C\n## L\n- n s n s\n  = noir (chut) noir (chut)\n")
    lyrics = [(n.findtext("lyric/syllabic"), n.findtext("lyric/text")) for n in root.iter("note")]
    assert lyrics == [("single", "noir"), ("single", "chut"), ("single", "noir"), ("single", "chut")]
