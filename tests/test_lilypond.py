import re

import pytest

from solfege.cahier import parse_cahier
from solfege.erreurs import CahierError
from solfege.lilypond import cahier_to_lilypond, lesson_to_lilypond

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
    """.ly (texte) d'un cahier donné en texte (ici, une seule leçon)."""
    return cahier_to_lilypond(parse_cahier(text))


def rythme_block(ly: str) -> str:
    """Le contenu de la variable ``rythme = { ... }`` (une seule leçon, sur un ou deux niveaux d'accolades)."""
    match = re.search(r"rythme = \{(.*?)\n\}\n", ly, re.DOTALL)
    assert match, ly
    return match.group(1)


def paroles_block(ly: str) -> str:
    match = re.search(r"paroles = \\lyricmode \{(.*?)\n\}\n", ly, re.DOTALL)
    assert match, ly
    return match.group(1).strip()


def hidden_block(ly: str) -> str:
    match = re.search(r"cachee = \{(.*?)\n\}\n", ly, re.DOTALL)
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
    """Toutes les notes utilisent le même piton (« c' », seul à tomber au milieu de l'unique
    ligne avec la clé de percussion), seule la durée varie."""
    rythme = rythme_block(ly)
    notes = re.findall(r"c'\d[\d.\[\]]*", rythme)
    assert notes  # au moins une note
    assert all(re.fullmatch(r"c'\d+\.?[\[\]]?", n) for n in notes)


def test_ligatures(ly):
    rythme = rythme_block(ly)
    # 2/4 : « c. d c d d | d d c n » -> groupes [c. d] et [c d d], puis [d d c]
    assert "c'8.[ c'16] c'8[ c'16 c'16]" in rythme
    assert "c'16[ c'16 c'8] c'4" in rythme


def test_double_barre_en_fin_d_exercice(ly):
    rythme = rythme_block(ly)
    assert rythme.count(r'\bar "|."') == 2


def test_pause_de_mesure(ly):
    rythme = rythme_block(ly)
    assert "R2." in rythme  # pause en 3/4 = 3 temps


def test_triolet(ly):
    rythme = rythme_block(ly)
    assert "TupletBracket.bracket-visibility = ##f" in rythme
    assert r"\tuplet 3/2 { c'8[ c'8 c'8] }" in rythme


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


def test_une_page_par_lecon_dans_un_seul_document():
    """Un seul .ly pour tout le cahier : réglages communs une fois, puis un \\bookpart (nouvelle page)
    par leçon, qui écrit son nombre de pages dans le journal (détection des débordements)."""
    ly = ly_of("# C\n## L\n- n n n n\n## M\n- r\n# D\n## N\n- b b\n")
    assert ly.count("\\version") == ly.count("set-paper-size") == ly.count("tagline") == 1
    assert ly.count("\\bookpart {") == 3
    assert re.findall(r'ly:message "solfege-pages (\S+) ~a"', ly) == ["1.1", "1.2", "2.1"]
    assert ly.count("rythme = {") == 3  # variables redéfinies avant chaque page
    assert ly.count("{") == ly.count("}")


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


def test_syllabe_chuchotee_sous_une_pause():
    """Bug réel (rendu visuel) : \\addlyrics/\\lyricsto saute toujours un silence, même correctement
    positionné dans la liste des paroles — la syllabe glissait alors sur la note suivante (« chut »
    affiché sous la ronde de l'exercice suivant au lieu de la pause). Fixé par une piste invisible
    (« cachee », en notes uniquement) à laquelle les paroles sont maintenant rattachées : voir
    « test_piste_invisible_pour_les_paroles »."""
    ly = ly_of("# C\n## L\n- r | r | p\n  = ron-de_lon-gue | ron-de_lon-gue | (chut)\n")
    assert paroles_block(ly) == '"ron-de lon-gue" "ron-de lon-gue" chut'


def test_piste_invisible_pour_les_paroles():
    """Les paroles sont rattachées à une piste « cachee » (NullVoice, jamais imprimée) qui ne
    contient que des notes, jamais de silence : c'est elle que \\lyricsto suit, pas la portée
    imprimée (où un silence, « r » ou « R », ne consomme jamais de syllabe)."""
    ly = ly_of("# C\n## L\n- r | p\n  = ron-de_lon-gue | (chut)\n")
    assert '\\new NullVoice = "cachee" \\cachee' in ly
    assert '\\lyricsto "cachee" \\paroles' in ly
    hidden = hidden_block(ly)
    assert re.fullmatch(r"(c'\d+\.? ?\|? ?)+", hidden), hidden
    assert "r" not in re.sub(r"c'\d+\.?", "", hidden)  # aucun silence dans la piste cachée


def test_syllabe_alignee_a_gauche_de_sa_note():
    """Bug réel (rendu visuel, pixel) : par défaut LilyPond centre une syllabe longue (ex.
    « ron-de lon-gue » sous une seule ronde) sur la colonne de la note, si bien que le début du
    mot se retrouve après la note plutôt que dessous. Fixé en forçant l'alignement à gauche du
    contexte Lyrics : `\\new Lyrics \\with { ... self-alignment-X = #LEFT }`."""
    ly = ly_of("# C\n## L\n- r\n  = ron-de_lon-gue\n")
    assert "\\new Lyrics \\with {\n" in ly
    assert "\\override LyricText.self-alignment-X = #LEFT" in ly
