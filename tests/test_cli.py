import shutil
from pathlib import Path

import pytest

from solfege import config
from solfege.cahier import load_cahier
from solfege.cli import main
from solfege.rendu import find_tool

ROOT = Path(__file__).resolve().parent.parent
CAHIER = ROOT / "cahier.txt"


def test_check_ok(capsys):
    assert main(["check", "--cahier", str(CAHIER)]) == 0
    assert "OK" in capsys.readouterr().out


def test_check_erreurs_toutes_affichees(tmp_path, capsys):
    bad = tmp_path / "cahier.txt"
    bad.write_text("# C\n## L\n- n n n\n- b b b\n", encoding="utf-8")
    assert main(["check", "--cahier", str(bad)]) == 1
    err = capsys.readouterr().err.splitlines()
    assert len(err) == 2
    assert "ligne 3" in err[0] and "ligne 4" in err[1]


def test_xml_ecrit_une_page_par_lecon(tmp_path):
    (tmp_path / "page_99.musicxml").write_text("ancienne page")
    assert main(["xml", "--cahier", str(CAHIER), "--build", str(tmp_path)]) == 0
    pages = sorted(p.name for p in tmp_path.glob("page_*.musicxml"))
    n_lessons = sum(1 for _ in load_cahier(CAHIER).lessons())
    assert pages == [f"page_{i:02d}.musicxml" for i in range(1, n_lessons + 1)]


def test_outil_introuvable(monkeypatch):
    monkeypatch.delenv("MSCORE", raising=False)
    from solfege.erreurs import RenduError

    with pytest.raises(RenduError, match="Outil introuvable"):
        find_tool("MSCORE", ["/nulle/part/mscore"])


def _available(env, candidates):
    try:
        find_tool(env, candidates)
        return True
    except Exception:
        return False


@pytest.mark.rendu
@pytest.mark.skipif(
    not (_available("MSCORE", config.MSCORE_CANDIDATES) and shutil.which("qpdf")), reason="MuseScore 4 ou qpdf absent"
)
def test_pdf_complet(tmp_path):
    cahier = tmp_path / "cahier.txt"
    cahier.write_text("# C\n## L\nConsigne : test\n- r | b b | n n c c n | t t t d d c c. d n\n", encoding="utf-8")
    out = tmp_path / "out.pdf"
    assert main(["pdf", "--cahier", str(cahier), "--build", str(tmp_path / "b"), "--output", str(out)]) == 0
    assert out.read_bytes().startswith(b"%PDF")
