"""Référence binaire : le .ly de tests/golden/exemple.txt doit rester identique octet pour octet.

Sert à vérifier qu'un refactor (ou une régénération complète du code) produit exactement
le même rendu. Pour mettre à jour la référence après un changement voulu du rendu :
    python3 -m pytest tests/test_golden.py --regenerer-golden
"""

import pytest

from solfege.cahier import load_cahier
from solfege.lilypond import cahier_to_lilypond

from .conftest import GOLDEN_DIR


def test_exemple_identique(request):
    expected = GOLDEN_DIR / "exemple.ly"
    actual = cahier_to_lilypond(load_cahier(GOLDEN_DIR / "exemple.txt"))
    if request.config.getoption("--regenerer-golden"):
        expected.write_text(actual, encoding="utf-8")
        return
    if not expected.exists():
        pytest.fail(f"{expected} manquant : lancer pytest --regenerer-golden")
    assert actual == expected.read_text(encoding="utf-8"), f"{expected.name} a changé (rendu modifié ?)"
