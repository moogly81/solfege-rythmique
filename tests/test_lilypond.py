import re

import pytest

from solfege.cahier import parse_cahier
from solfege.erreurs import CahierError
from solfege.lilypond import lesson_to_lilypond

CAHIER = """\
# Chapitre 1 : Tout <mélangé> & co
## Essai
Consigne : Regarde le chiffrage !
Mesure : 3/4
- b. | p | t t t n n
  n. c n
- 2/4 : c. d c d d | d d c n
"""


def ly_of(text: str) -> str:
    """.ly (texte) de la 1re leçon d'un cahier donné en texte."""
    chapter = parse_cahier(text).chapters[0]
    return lesson_to_lilypond(chapter, chapter.lessons[0])


def rythme_block(ly: str) -> str:
    """Le contenu de la variable ``rythme = { ... }`` (une seule leçon, sur un ou deux niveaux d'accolades)."""
    match = re.search(r"rythme = \{(.*?)\n\}\n", ly, re.DOTALL)
    assert match, ly
    return match.group(1)


def paroles_block(ly: str) -> str:
    match = re.search(r"paroles = \\lyricmode \{(.*?)\n\}\n", ly, re.DOTALL)
    assert match, ly
    return match.group(1).strip()


@pytest.fixture
def ly():
    return ly_of(CAHIER)


def test_accolades_equilibrees(ly):
    assert ly.count("{") == ly.count("}")


def test_nouvelles_lignes(ly):
    """2 sauts de système : 2e ligne de l'exercice 1, puis exercice 2 (jamais avant la toute 1re ligne)."""
    rythme = rythme_block(ly)
    assert rythme.count(r"\break") == 2
    assert not rythme.lstrip().startswith(r"\break")


def test_reperes_et_chiffrages(ly):
    rythme = rythme_block(ly)
    assert re.findall(r'\\box "([\d.]+)"', rythme) == ["1.1.1", "1.1.2"]
    assert re.findall(r"\\time (\S+)", rythme) == ["3/4", "2/4"]


def test_portee_de_rythme(ly):
    """1 ligne, clé de percussion, hampes forcées en haut : réglages globaux, une seule fois."""
    rythme = rythme_block(ly)
    assert rythme.count("Staff.StaffSymbol.line-count = #1") == 1
    assert rythme.count('\\clef "percussion"') == 1
    assert rythme.count("Stem.direction = #UP") == 1
    assert r"\autoBeamOff" in rythme


def test_notes_sur_pitch_fixe(ly):
    """Toutes les notes utilisent le même piton (« b », seul à tomber sur l'unique ligne avec la
    clé de percussion), seule la durée varie."""
    rythme = rythme_block(ly)
    notes = re.findall(r"\bb\d[\d.\[\]]*", rythme)  # un chiffre après le « b » : exclut « break »...
    assert notes  # au moins une note
    assert all(re.fullmatch(r"b\d+\.?[\[\]]?", n) for n in notes)


def test_ligatures(ly):
    rythme = rythme_block(ly)
    # 2/4 : « c. d c d d | d d c n » -> groupes [c. d] et [c d d], puis [d d c]
    assert "b8.[ b16] b8[ b16 b16]" in rythme
    assert "b16[ b16 b8] b4" in rythme


def test_double_barre_en_fin_d_exercice(ly):
    rythme = rythme_block(ly)
    assert rythme.count(r'\bar "|."') == 2


def test_pause_de_mesure(ly):
    rythme = rythme_block(ly)
    assert "R2." in rythme  # pause en 3/4 = 3 temps


def test_triolet(ly):
    rythme = rythme_block(ly)
    assert "TupletBracket.bracket-visibility = ##f" in rythme
    assert r"\tuplet 3/2 { b8[ b8 b8] }" in rythme


def test_en_tete_trois_tailles(ly):
    assert 'abs-fontsize #12 "Chapitre 1 · Tout <mélangé> & co"' in ly
    assert 'abs-fontsize #22 \\bold "1.1  Essai"' in ly
    assert 'abs-fontsize #13 \\italic "Regarde le chiffrage !"' in ly


def test_mise_en_page_a4(ly):
    assert '#(set-paper-size "a4")' in ly
    assert "top-margin = 15\\mm" in ly


def test_taille_de_portee():
    ly = ly_of("# C\n## L\n- n n n n\n")
    (taille,) = re.findall(r"set-global-staff-size ([\d.]+)", ly)
    assert float(taille) == pytest.approx(8.5 * 72 / 25.4, abs=0.01)


def test_nom_de_sortie_force():
    """page_stem force \\bookOutputName : nécessaire pour LilyPond 2.24 (Ubuntu 24.04, CI), qui
    déduit mal le nom du 2e fichier (et suivants) compilé dans le même appel (\"lilypond
    --output DIR a.ly b.ly\"), sans quoi le PDF du 2e fichier n'est jamais écrit."""
    chapter = parse_cahier("# C\n## L\n- n n n n\n").chapters[0]
    ly_sans = lesson_to_lilypond(chapter, chapter.lessons[0])
    ly_avec = lesson_to_lilypond(chapter, chapter.lessons[0], page_stem="page_02")
    assert r"\bookOutputName" not in ly_sans
    assert '\\bookOutputName "page_02"' in ly_avec


def test_rythme_faux_refuse():
    cahier = parse_cahier("# C\n## L\n- n n n\n")
    chapter = cahier.chapters[0]
    with pytest.raises(CahierError, match="3 temps au lieu de 4"):
        lesson_to_lilypond(chapter, chapter.lessons[0])


def test_syllabes_sous_les_notes():
    ly = ly_of("# C\n## L\n- d d d d s n n\n  = qua- tre dou- bles & 3\n")
    assert paroles_block(ly) == r'qua -- tre dou -- bles \skip 4 & "3"'


def test_syllabe_numerique_entre_guillemets():
    """Un mot tout en chiffres (compte de temps) doit être entre guillemets : sinon LilyPond le lit
    comme la durée du mot précédent, pas comme un nouveau mot."""
    ly = ly_of("# C\n## L\nMesure : 3/4\n- n n n\n  = 1 2 3\n")
    assert paroles_block(ly) == '"1" "2" "3"'


def test_syllabe_avec_espace():
    ly = ly_of("# C\n## L\n- r\n  = ron-de_lon-gue\n")
    assert paroles_block(ly) == '"ron-de lon-gue"'


def test_syllabe_chuchotee_sous_un_silence():
    ly = ly_of("# C\n## L\n- n s n s\n  = noir (chut) noir (chut)\n")
    assert paroles_block(ly) == "noir chut noir chut"


def test_silence_sans_syllabe_est_saute():
    """Sans ligne de syllabes du tout, chaque silence est un « \\skip », pas un mot."""
    ly = ly_of("# C\n## L\n- n n s n\n")
    assert paroles_block(ly) == r"\skip 4 \skip 4 \skip 4 \skip 4"
