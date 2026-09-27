import pytest

from solfege.cahier import parse_cahier
from solfege.erreurs import CahierError
from solfege.rythme import BEAT, check, compute_beams, parse_line, parse_time


@pytest.mark.parametrize(("sig", "beats"), [("2/4", 2), ("3/4", 3), ("4/4", 4)])
def test_parse_time(sig, beats):
    assert parse_time(sig, "ici") == beats


@pytest.mark.parametrize(
    ("sig", "message"),
    [
        ("trois", "chiffrage invalide « trois »"),
        ("6/8", r"seuls les chiffrages en /4 sont gérés \(6/8\)"),
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
    ],
)
def test_lignes_invalides(line, beats, message):
    with pytest.raises(CahierError, match=f"^ici, {message}" if "mesure" in message else message):
        parse_line(line, beats, "ici")


def test_check_rassemble_toutes_les_erreurs():
    cahier = parse_cahier("# C\n## L\n- n n n\n  r\n- 5/8 : r\n- x\n")
    errors = check(cahier)
    assert len(errors) == 3
    assert errors[0].startswith("cahier.txt, ligne 3 (exercice 1.1.1), mesure 1")
    assert "chiffrage invalide" not in errors[1] and "/4" in errors[1]
    assert "symbole inconnu « x »" in errors[2]


def test_check_ok():
    assert check(parse_cahier("# C\n## L\n- r | b b\n  n n n n\n")) == []


def beams(tokens):
    return [dict(b) for b in compute_beams(tokens.split())]


def test_ligatures_par_temps():
    assert beams("c c c c n n") == [{1: "begin"}, {1: "end"}, {1: "begin"}, {1: "end"}, {}, {}]


def test_ligatures_doubles():
    assert beams("d d d d") == [
        {1: "begin", 2: "begin"},
        {1: "continue", 2: "continue"},
        {1: "continue", 2: "continue"},
        {1: "end", 2: "end"},
    ]
    assert beams("c d d") == [{1: "begin"}, {1: "continue", 2: "begin"}, {1: "end", 2: "end"}]
    assert beams("d d c") == [{1: "begin", 2: "begin"}, {1: "continue", 2: "end"}, {1: "end"}]


def test_ligatures_croche_pointee_double():
    assert beams("c. d") == [{1: "begin"}, {1: "end", 2: "backward hook"}]
    assert beams("d c.") == [{1: "begin", 2: "forward hook"}, {1: "end"}]


def test_ligatures_triolet():
    assert beams("t t t") == [{1: "begin"}, {1: "continue"}, {1: "end"}]


def test_silence_coupe_la_ligature():
    assert beams("ds c c c") == [{}, {}, {1: "begin"}, {1: "end"}]
    assert BEAT == 12
