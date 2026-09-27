import subprocess
from pathlib import Path

import pytest

from solfege import config, rendu
from solfege.cahier import load_cahier
from solfege.cli import main
from solfege.erreurs import RenduError
from solfege.rendu import find_tool, merge_pdfs, overflow_warnings, render_pdfs

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
    assert main(["xml", "--cahier", str(bad), "--build", str(build)]) == 1
    assert not build.exists()


def test_xml_ecrit_une_page_par_lecon(tmp_path):
    (tmp_path / "page_99.musicxml").write_text("ancienne page")
    assert main(["xml", "--cahier", str(CAHIER_PATH), "--build", str(tmp_path)]) == 0
    pages = sorted(p.name for p in tmp_path.glob("page_*.musicxml"))
    n_lessons = sum(1 for _ in load_cahier(CAHIER_PATH).lessons())
    assert pages == [f"page_{i:02d}.musicxml" for i in range(1, n_lessons + 1)]


# --- find_tool ---------------------------------------------------------------


def test_outil_introuvable(monkeypatch):
    monkeypatch.delenv("MSCORE", raising=False)
    with pytest.raises(RenduError, match=r"^Outil introuvable \(MSCORE\) : MuseScore 4\. Installez-le"):
        find_tool("MSCORE", ["/nulle/part/mscore"])


def test_variable_d_environnement_valide(monkeypatch, tmp_path):
    tool = tmp_path / "mon-mscore"
    tool.touch()
    monkeypatch.setenv("MSCORE", str(tool))
    assert find_tool("MSCORE", ["/nulle/part/mscore"]) == str(tool)


def test_variable_d_environnement_fausse_refusee(monkeypatch):
    monkeypatch.setenv("QPDF", "/nulle/part/qpdf")
    with pytest.raises(RenduError, match="qpdf introuvable : la variable QPDF pointe sur « /nulle/part/qpdf »"):
        find_tool("QPDF", ["qpdf"])


# --- rendu sans MuseScore (subprocess simulé) --------------------------------


@pytest.fixture
def fake_tools(monkeypatch, tmp_path):
    """MuseScore et qpdf remplacés par des fichiers vides ; subprocess.run enregistré."""
    calls: list[list[str]] = []
    for name in ("mscore", "qpdf"):
        (tmp_path / name).touch()
    monkeypatch.setenv("MSCORE", str(tmp_path / "mscore"))
    monkeypatch.setenv("QPDF", str(tmp_path / "qpdf"))

    class Fake:
        returncode = 0
        stdout = "1\n"
        stderr = ""
        writes_pdfs = True

    def run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[0].endswith("mscore") and Fake.writes_pdfs:
            for job in __import__("json").loads(Path(cmd[cmd.index("-j") + 1]).read_text()):
                Path(job["out"]).write_bytes(b"%PDF-fake")
        return subprocess.CompletedProcess(cmd, Fake.returncode, Fake.stdout, Fake.stderr)

    monkeypatch.setattr(rendu.subprocess, "run", run)
    Fake.calls = calls
    return Fake


def test_render_pdfs_un_seul_appel_et_nettoyage(fake_tools, tmp_path):
    build = tmp_path / "b"
    build.mkdir()
    (build / "page_09.pdf").write_bytes(b"perime")
    xmls = [build / "page_01.musicxml", build / "page_02.musicxml"]
    for x in xmls:
        x.write_text("<x/>")
    pdfs = render_pdfs(xmls, build)
    assert pdfs == [build / "page_01.pdf", build / "page_02.pdf"]
    assert all(p.exists() for p in pdfs)
    assert not (build / "page_09.pdf").exists()
    (cmd,) = fake_tools.calls
    assert cmd[1:4] == ["-S", str((build / "style.mss").resolve()), "-j"]
    assert Path(cmd[4]).is_absolute()
    assert (build / "style.mss").read_text(encoding="utf-8") == config.STYLE_MSS


def test_render_pdfs_code_retour_non_nul_tolere(fake_tools, tmp_path, capsys):
    fake_tools.returncode = -6  # SIGABRT à la fermeture : les PDF sont là
    xml = tmp_path / "page_01.musicxml"
    xml.write_text("<x/>")
    render_pdfs([xml], tmp_path)
    out, err = capsys.readouterr()
    assert out == "" and "code -6" in err and "bug connu" in err


def test_render_pdfs_pdf_manquant(fake_tools, tmp_path):
    fake_tools.writes_pdfs = False
    xml = tmp_path / "page_01.musicxml"
    xml.write_text("<x/>")
    with pytest.raises(RenduError, match=r"MuseScore n'a pas produit : .*page_01\.pdf \(voir .*mscore\.log\)"):
        render_pdfs([xml], tmp_path)


def test_merge_pdfs_echec_sans_trace(fake_tools, tmp_path):
    fake_tools.returncode = 2
    fake_tools.stderr = "qpdf: fichier illisible"
    with pytest.raises(RenduError, match=r"qpdf n'a pas pu fusionner les pages \(code 2\) : qpdf: fichier illisible"):
        merge_pdfs([tmp_path / "a.pdf"], tmp_path / "out.pdf")


def test_merge_pdfs_commande(fake_tools, tmp_path):
    merge_pdfs([tmp_path / "a.pdf", tmp_path / "b.pdf"], tmp_path / "out.pdf")
    (cmd,) = fake_tools.calls
    assert cmd[1:] == [
        "--empty",
        "--pages",
        str(tmp_path / "a.pdf"),
        str(tmp_path / "b.pdf"),
        "--",
        str(tmp_path / "out.pdf"),
    ]


def test_debordement_signale(fake_tools, tmp_path):
    fake_tools.stdout = "2\n"
    assert overflow_warnings([tmp_path / "page_03.pdf"], ["1.3"]) == [
        "Attention : la leçon 1.3 déborde (2 pages au lieu de 1) : raccourcir des lignes."
    ]
    fake_tools.stdout = "1\n"
    assert overflow_warnings([tmp_path / "page_03.pdf"], ["1.3"]) == []


def test_outil_qui_ne_se_lance_pas(fake_tools, monkeypatch, tmp_path):
    def run(cmd, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(rendu.subprocess, "run", run)
    with pytest.raises(RenduError, match=r"Impossible de lancer « .*qpdf » : Permission denied"):
        merge_pdfs([tmp_path / "a.pdf"], tmp_path / "out.pdf")


# --- rendu réel --------------------------------------------------------------


def _available(env, candidates):
    try:
        find_tool(env, candidates)
        return True
    except RenduError:
        return False


@pytest.mark.rendu
@pytest.mark.skipif(
    not (_available("MSCORE", config.MSCORE_CANDIDATES) and _available("QPDF", config.QPDF_CANDIDATES)),
    reason="MuseScore 4 ou qpdf absent",
)
def test_pdf_complet(tmp_path):
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
    assert rendu.page_count(out) == 2
    assert [rendu.page_count(p) for p in sorted(build.glob("page_*.pdf"))] == [1, 1]
