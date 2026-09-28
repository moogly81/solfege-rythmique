import re
import subprocess
from pathlib import Path

import pytest

from solfege import config, rendu
from solfege.cahier import load_cahier
from solfege.cli import main
from solfege.erreurs import RenduError
from solfege.rendu import find_tool, overflow_warnings, render_pdf

from .conftest import CAHIER_PATH


def test_check_ok(capsys):
    assert main(["check", "--cahier", str(CAHIER_PATH)]) == 0
    assert "OK" in capsys.readouterr().out


def test_check_erreurs_toutes_affichees(tmp_path, capsys):
    bad = tmp_path / "cahier.txt"
    bad.write_text("# C\n## L\n- n n n\n- b b b\n", encoding="utf-8")
    assert main(["check", "--cahier", str(bad)]) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert "Traceback" not in err
    assert err.splitlines() == [
        f"{bad}, ligne 3 (exercice 1.1.1), mesure 1 (n n n) : 3 temps au lieu de 4",
        f"{bad}, ligne 4 (exercice 1.1.2), mesure 1 (b b b) : 6 temps au lieu de 4",
    ]


def test_erreur_ne_cree_aucun_fichier(tmp_path):
    bad = tmp_path / "cahier.txt"
    bad.write_text("# C\n## L\n- n n n\n", encoding="utf-8")
    build = tmp_path / "build"
    assert main(["ly", "--cahier", str(bad), "--build", str(build)]) == 1
    assert not build.exists()


def test_ly_ecrit_un_seul_fichier(tmp_path):
    (tmp_path / "page_99.ly").write_text("reste de l'ancien rendu page par page")
    assert main(["ly", "--cahier", str(CAHIER_PATH), "--build", str(tmp_path)]) == 0
    assert sorted(p.name for p in tmp_path.glob("*.ly")) == ["cahier.ly"]
    n_lessons = sum(1 for _ in load_cahier(CAHIER_PATH).lessons())
    assert (tmp_path / "cahier.ly").read_text(encoding="utf-8").count("\\bookpart {") == n_lessons


# --- find_tool ---------------------------------------------------------------


def test_outil_introuvable(monkeypatch):
    monkeypatch.delenv("LILYPOND", raising=False)
    with pytest.raises(RenduError, match=r"^Outil introuvable \(LILYPOND\) : LilyPond\. Installez-le"):
        find_tool("LILYPOND", ["/nulle/part/lilypond"])


def test_variable_d_environnement_valide(monkeypatch, tmp_path):
    tool = tmp_path / "mon-lilypond"
    tool.touch()
    monkeypatch.setenv("LILYPOND", str(tool))
    assert find_tool("LILYPOND", ["/nulle/part/lilypond"]) == str(tool)


def test_variable_d_environnement_fausse_refusee(monkeypatch):
    monkeypatch.setenv("LILYPOND", "/nulle/part/lilypond")
    message = "LilyPond introuvable : la variable LILYPOND pointe sur « /nulle/part/lilypond »"
    with pytest.raises(RenduError, match=message):
        find_tool("LILYPOND", ["lilypond"])


# --- rendu sans LilyPond (subprocess simulé) ---------------------------------


@pytest.fixture
def fake_lilypond(monkeypatch, tmp_path):
    """LilyPond remplacé par un fichier vide ; subprocess.run enregistré. Le faux LilyPond écrit le PDF
    et, dans le journal, le nombre de pages de chaque leçon (« solfege-pages N.M K »)."""
    calls: list[list[str]] = []
    (tmp_path / "lilypond").touch()
    monkeypatch.setenv("LILYPOND", str(tmp_path / "lilypond"))

    class Fake:
        returncode = 0
        writes_pdf = True
        log = "solfege-pages 1.1 1\nsolfege-pages 1.2 2\n"

    def run(cmd, **kwargs):
        calls.append(cmd)
        if Fake.writes_pdf:
            (Path(cmd[2]) / Path(cmd[3]).with_suffix(".pdf").name).write_bytes(b"%PDF-fake")
        kwargs["stdout"].write(Fake.log)
        return subprocess.CompletedProcess(cmd, Fake.returncode)

    monkeypatch.setattr(rendu.subprocess, "run", run)
    Fake.calls = calls
    return Fake


def test_render_pdf_un_seul_appel_et_nettoyage(fake_lilypond, tmp_path):
    build = tmp_path / "b"
    build.mkdir()
    (build / "page_09.pdf").write_bytes(b"perime")
    ly = build / "cahier.ly"
    ly.write_text("% vide")
    pdf, pages = render_pdf(ly, build)
    assert pdf == build / "cahier.pdf"
    assert pdf.read_bytes() == b"%PDF-fake"
    assert pages == {"1.1": 1, "1.2": 2}
    assert not (build / "page_09.pdf").exists()
    (cmd,) = fake_lilypond.calls
    assert cmd[1] == "--output"
    assert Path(cmd[2]).is_absolute()
    assert cmd[3:] == [str(ly.resolve())]


def test_render_pdf_supprime_l_ancien_pdf(fake_lilypond, tmp_path):
    fake_lilypond.writes_pdf = False
    (tmp_path / "cahier.pdf").write_bytes(b"perime")
    ly = tmp_path / "cahier.ly"
    ly.write_text("% vide")
    with pytest.raises(RenduError, match=r"LilyPond n'a pas produit : .*cahier\.pdf \(voir .*lilypond\.log\)"):
        render_pdf(ly, tmp_path)
    assert not (tmp_path / "cahier.pdf").exists()


def test_render_pdf_code_retour_non_nul_echoue(fake_lilypond, tmp_path):
    fake_lilypond.returncode = 1
    ly = tmp_path / "cahier.ly"
    ly.write_text("% vide")
    with pytest.raises(RenduError, match=r"LilyPond a échoué \(code 1\) : voir .*lilypond\.log"):
        render_pdf(ly, tmp_path)


def test_debordement_signale():
    assert overflow_warnings({"1.1": 1, "1.3": 2}, ["1.1", "1.3"]) == [
        "Attention : la leçon 1.3 déborde (2 pages au lieu de 1) : raccourcir des lignes."
    ]
    assert overflow_warnings({"1.1": 1, "1.3": 1}, ["1.1", "1.3"]) == []


def test_nombre_de_pages_inconnu():
    with pytest.raises(RenduError, match=r"LilyPond n'a pas indiqué le nombre de pages de la leçon 1\.3"):
        overflow_warnings({"1.1": 1}, ["1.1", "1.3"])


def test_outil_qui_ne_se_lance_pas(fake_lilypond, monkeypatch, tmp_path):
    def run(cmd, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(rendu.subprocess, "run", run)
    ly = tmp_path / "cahier.ly"
    ly.write_text("% vide")
    with pytest.raises(RenduError, match=r"Impossible de lancer « .*lilypond » : Permission denied"):
        render_pdf(ly, tmp_path)


# --- rendu réel --------------------------------------------------------------


def _available(env, candidates):
    try:
        find_tool(env, candidates)
        return True
    except RenduError:
        return False


def _pdf_pages(pdf: Path) -> int:
    """Nombre de pages d'un PDF 1.4 (celui de LilyPond : pas de flux d'objets compressés)."""
    return max(int(n) for n in re.findall(rb"/Count (\d+)", pdf.read_bytes()))


needs_lilypond = pytest.mark.skipif(not _available("LILYPOND", config.LILYPOND_CANDIDATES), reason="LilyPond absent")


@pytest.mark.rendu
@needs_lilypond
def test_pdf_complet(tmp_path, capsys):
    cahier = tmp_path / "cahier.txt"
    cahier.write_text(
        "# C\n## L\nConsigne : test\n- r | b b | n n c c n | t t t d d c c. d n\n"
        "  = 1 | 1 2 | 1 2 3 4 5 | 1 2 3 4 5 6 7 8 9\n"
        "## M\n- 3/4 : b. | p | c n c s | n. c n\n  = 1 | (chut) | 1 2 3 | 1 2 3\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.pdf"
    build = tmp_path / "b"
    assert main(["pdf", "--cahier", str(cahier), "--build", str(build), "--output", str(out)]) == 0
    assert out.read_bytes().startswith(b"%PDF")
    assert _pdf_pages(out) == 2
    assert f"PDF généré : {out} (2 pages)" in capsys.readouterr().out


@pytest.mark.rendu
@needs_lilypond
def test_pdf_debordement_reel(tmp_path, capsys):
    """Une leçon trop longue : LilyPond la met sur 2 pages, le programme le dit (code 2)."""
    cahier = tmp_path / "cahier.txt"
    trop_long = "".join("- n n n n | b b | r | c c c c b\n  n n b | r | b b | n n n n\n" for _ in range(12))
    cahier.write_text(f"# C\n## Courte\n- r | b b\n## Longue\n{trop_long}", encoding="utf-8")
    out = tmp_path / "out.pdf"
    assert main(["pdf", "--cahier", str(cahier), "--build", str(tmp_path / "b"), "--output", str(out)]) == 2
    err = capsys.readouterr().err
    assert "la leçon 1.2 déborde" in err
    assert "1.1" not in err
    assert _pdf_pages(out) > 2
