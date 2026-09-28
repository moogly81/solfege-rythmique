import pytest

from solfege.cahier import parse_cahier
from solfege.erreurs import CahierError
from solfege.rythme import BEAT, beam_groups, check, parse_line, parse_syllables, parse_time


@pytest.mark.parametrize(("sig", "beats"), [("2/4", 2), ("3/4", 3), ("4/4", 4)])
def test_parse_time(sig, beats):
    assert parse_time(sig, "ici") == beats


@pytest.mark.parametrize(
    ("sig", "message"),
    [
        ("trois", "chiffrage invalide « trois »"),
        ("6/8", r"seuls les chiffrages en /4 sont gérés \(6/8\)"),
        ("0/4", r"chiffrage invalide « 0/4 » \(de 1 à 12 temps par mesure\)"),
        ("-3/4", "chiffrage invalide « -3/4 »"),
        ("13/4", "chiffrage invalide « 13/4 »"),
    ],
)
def test_parse_time_invalide(sig, message):
    with pytest.raises(CahierError, match=message):
        parse_time(sig, "ici")


@pytest.mark.parametrize(
    ("line", "beats"),
    [
        ("r | b b | n n n n | p", 4),
        ("b. n | n. c b | c. d n n n | dp n s", 4),
        ("c d d d d c | t t t c c | ds c s", 2),
        ("p | b n", 3),
    ],
)
def test_lignes_valides(line, beats):
    measures = parse_line(line, beats, "ici")
    assert len(measures) == line.count("|") + 1


@pytest.mark.parametrize(
    ("line", "beats", "message"),
    [
        ("b n n", 3, r"mesure 1 \(b n n\) : 4 temps au lieu de 3"),
        ("r | n n", 4, r"mesure 2 \(n n\) : 2 temps au lieu de 4"),
        ("n nn n n", 4, "symbole inconnu « nn »"),
        ("p n", 4, "la pause « p » doit être seule"),
        ("t t n n n", 4, "un triolet = 3 « t » au début d'un temps"),
        ("c t t t c n n", 4, "un triolet = 3 « t » au début d'un temps"),
        ("n n | | n n", 2, r"mesure 2 : mesure vide \(deux barres « \| » à la suite \?\)"),
        ("n n |", 2, r"mesure 2 : mesure vide"),
    ],
)
def test_lignes_invalides(line, beats, message):
    with pytest.raises(CahierError, match=f"^ici, {message}" if "mesure" in message else message):
        parse_line(line, beats, "ici")


def test_check_rassemble_toutes_les_erreurs():
    cahier = parse_cahier("# C\n## L\n- n n n\n  r\n- 5/8 : r\n- x\n")
    errors = check(cahier)
    assert errors == [
        "cahier.txt, ligne 3 (exercice 1.1.1), mesure 1 (n n n) : 3 temps au lieu de 4",
        "cahier.txt, ligne 5 (exercice 1.1.2) : seuls les chiffrages en /4 sont gérés (5/8)",
        "cahier.txt, ligne 6 (exercice 1.1.3), mesure 1 (x) : symbole inconnu « x »",
    ]


def test_titre_trop_large_refuse():
    long_title = "Révision : rondes, blanches, pauses et demi-pauses"  # ≈ 219 mm en gras 22 pt
    (error,) = check(parse_cahier(f"# C\n## {long_title}\n- r\n"))
    assert error == (
        "cahier.txt, ligne 2 : le titre de la leçon est trop large pour la page "
        "(≈ 219 mm, maximum 180 mm) : le raccourcir"
    )


def test_consigne_trop_large_refusee():
    consigne = "Frappe les notes, puis pendant les silences lève les bras et compte lentement dans ta tête, sans bruit."
    (error,) = check(parse_cahier(f"# C\n## L\nConsigne : {consigne}\n- r\n"))
    assert "la consigne est trop large pour la page (≈ 2" in error


def test_largeur_mesuree_avec_la_police_de_musescore():
    # Calibré sur un rendu réel : cette consigne (13 pt italique) fait 163 mm dans le PDF
    from solfege.largeurs import ITALIC, largeur_mm

    texte = "Compte 1 - 2 - 3 - 4. Dis « ron-de lon-gue », chuchote « chut » pendant la pause."
    assert 161 <= largeur_mm(texte, ITALIC, 13) <= 166


def test_check_ok():
    assert check(parse_cahier("# C\n## L\n- r | b b\n  n n n n\n")) == []


def groups(tokens):
    return beam_groups(tokens.split())


def test_ligatures_par_temps():
    assert groups("c c c c n n") == [[0, 1], [2, 3]]


def test_ligatures_doubles():
    assert groups("d d d d") == [[0, 1, 2, 3]]
    assert groups("c d d") == [[0, 1, 2]]
    assert groups("d d c") == [[0, 1, 2]]


def test_ligatures_croche_pointee_double():
    assert groups("c. d") == [[0, 1]]
    assert groups("d c.") == [[0, 1]]


def test_ligatures_triolet():
    assert groups("t t t") == [[0, 1, 2]]


def test_silence_coupe_la_ligature():
    assert groups("ds c c c") == [[2, 3]]
    assert BEAT == 12


def test_valeur_qui_chevauche_deux_temps_reste_dans_son_groupe():
    # c. commence dans le 1er temps et finit dans le 2e : la double qui suit reste ligaturée
    assert groups("c c. d n n") == [[0, 1, 2]]


@pytest.mark.parametrize("tokens", ["c n c", "n. c", "n c n", "c s c"])
def test_pas_de_ligature_entre_croches_isolees(tokens):
    assert groups(tokens) == []


def test_syllabes_une_par_note():
    # une entrée par symbole ; le silence n'a rien (None)
    assert parse_syllables("1 2 | 1", [["n", "s", "b"], ["r"]], "ici") == [["1", None, "2"], ["1"]]


def test_syllabe_entre_parentheses_sous_un_silence():
    assert parse_syllables("1 (chut) 2 | (chut)", [["n", "s", "b"], ["p"]], "ici") == [["1", "chut", "2"], ["chut"]]


@pytest.mark.parametrize(
    ("syllables", "message"),
    [
        ("1 2 3", "^ici : 1 mesures de syllabes pour 2 mesures de rythme"),
        ("1 2 3 | 1 2", r"^ici, mesure 1 \(1 2 3\) : 3 syllabes pour 2 notes"),
        ("1 - | 1", r"^ici, mesure 1 \(1 -\) : syllabe vide « - »"),
        ("1 (chut | 1", r"^ici, mesure 1 \(1 \(chut\) : parenthèse non fermée « \(chut »"),
        ("(chut) 1 2 | 1", r"« \(chut\) » : une syllabe entre parenthèses va sous un silence"),
        ("1 2 (chut) | 1", r"« \(chut\) » : une syllabe entre parenthèses va sous un silence"),
    ],
)
def test_syllabes_invalides(syllables, message):
    with pytest.raises(CahierError, match=message):
        parse_syllables(syllables, [["n", "s", "b"], ["r"]], "ici")


def test_check_verifie_les_syllabes():
    (error,) = check(parse_cahier("# C\n## L\n- n n b\n  = 1 2\n"))
    assert error == "cahier.txt, ligne 4 (syllabes de l'exercice 1.1.1), mesure 1 (1 2) : 2 syllabes pour 3 notes"
