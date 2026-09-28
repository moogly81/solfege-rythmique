"""Étape 4 : .ly -> PDF (LilyPond), et détection des leçons qui débordent de leur page."""

import os
import re
import shutil
import subprocess
from pathlib import Path

from . import config
from .erreurs import RenduError
from .lilypond import PAGES_MARKER

# Variable d'environnement -> (nom lisible, comment l'installer)
TOOLS = {
    "LILYPOND": ("LilyPond", "brew install lilypond (ou apt-get install lilypond)"),
}


def find_tool(env_var: str, candidates: list[str]) -> str:
    """Chemin de l'outil : la variable d'environnement si elle est définie, sinon les candidats."""
    name, install = TOOLS.get(env_var, (env_var, ""))
    forced = os.environ.get(env_var)
    if forced:
        if Path(forced).exists() or shutil.which(forced):
            return forced
        raise RenduError(f"{name} introuvable : la variable {env_var} pointe sur « {forced} », qui n'existe pas.")
    for c in candidates:
        if Path(c).exists() or shutil.which(c):
            return c
    raise RenduError(f"Outil introuvable ({env_var}) : {name}. Installez-le ({install}) ou définissez {env_var}.")


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """subprocess.run sans trace Python : un outil qui ne se lance pas devient une RenduError."""
    try:
        return subprocess.run(cmd, check=False, **kwargs)
    except OSError as e:
        raise RenduError(f"Impossible de lancer « {cmd[0]} » : {e.strerror or e}") from None


def render_pdf(ly_path: Path, build_dir: Path) -> tuple[Path, dict[str, int]]:
    """Compile le .ly du cahier en un seul PDF. Renvoie le PDF et le nombre de pages de chaque leçon,
    lu dans le journal LilyPond (lignes « solfege-pages N.M K » écrites par « page-post-process »)."""
    lilypond = find_tool("LILYPOND", config.LILYPOND_CANDIDATES)
    pdf = build_dir / ly_path.with_suffix(".pdf").name
    for old in [pdf, *build_dir.glob("page_*.pdf")]:
        old.unlink(missing_ok=True)  # jamais de PDF périmé (ni ceux de l'ancien rendu page par page)

    log_file = build_dir / "lilypond.log"
    with log_file.open("w", encoding="utf-8", errors="replace") as log:
        result = _run(
            [lilypond, "--output", str(build_dir.resolve()), str(ly_path.resolve())],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    if result.returncode != 0:
        raise RenduError(f"LilyPond a échoué (code {result.returncode}) : voir {log_file}")
    if not pdf.exists():
        raise RenduError(f"LilyPond n'a pas produit : {pdf} (voir {log_file})")
    log_text = log_file.read_text(encoding="utf-8", errors="replace")
    pages = {m[1]: int(m[2]) for m in re.finditer(rf"^{PAGES_MARKER} (\S+) (\d+)$", log_text, re.MULTILINE)}
    return pdf, pages


def overflow_warnings(pages: dict[str, int], labels: list[str]) -> list[str]:
    """Une leçon doit tenir sur une page : signale celles qui débordent."""
    warnings = []
    for label in labels:
        if label not in pages:
            raise RenduError(f"LilyPond n'a pas indiqué le nombre de pages de la leçon {label}")
        if pages[label] != 1:
            n = pages[label]
            warnings.append(f"Attention : la leçon {label} déborde ({n} pages au lieu de 1) : raccourcir des lignes.")
    return warnings
