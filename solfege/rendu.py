"""Étape 4 : MusicXML -> PDF (MuseScore 4) puis fusion des pages (qpdf)."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import config
from .erreurs import RenduError

# Variable d'environnement -> (nom lisible, comment l'installer)
TOOLS = {
    "MSCORE": ("MuseScore 4", "https://musescore.org, version 4.7.x testée"),
    "QPDF": ("qpdf", "brew install qpdf"),
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


def render_pdfs(xml_paths: list[Path], build_dir: Path) -> list[Path]:
    """Exporte chaque MusicXML en PDF, en un seul appel MuseScore (job JSON)."""
    mscore = find_tool("MSCORE", config.MSCORE_CANDIDATES)
    for old in build_dir.glob("page_*.pdf"):
        old.unlink()  # évite de fusionner des pages d'une version plus longue
    pdfs = [p.with_suffix(".pdf") for p in xml_paths]
    jobs = [{"in": str(x.resolve()), "out": str(p.resolve())} for x, p in zip(xml_paths, pdfs, strict=True)]

    style_file = build_dir / "style.mss"
    style_file.write_text(config.STYLE_MSS, encoding="utf-8")
    job_file = build_dir / "job.json"
    job_file.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    # MuseScore 4.7 peut avorter (SIGABRT, "mutex lock failed") dans exit(),
    # APRÈS avoir écrit les PDF : bug de destruction des statiques côté
    # MuseScore. On juge donc le résultat sur les fichiers, pas le code retour.
    log_file = build_dir / "mscore.log"
    with log_file.open("w", encoding="utf-8", errors="replace") as log:
        rc = _run(
            [mscore, "-S", str(style_file.resolve()), "-j", str(job_file.resolve())],
            stdout=log,
            stderr=subprocess.STDOUT,
        ).returncode
    missing = [str(p) for p in pdfs if not p.exists()]
    if missing:
        raise RenduError(f"MuseScore n'a pas produit : {', '.join(missing)} (voir {log_file})")
    if rc != 0:
        print(
            f"Note : MuseScore a quitté avec le code {rc} après export (bug connu à la fermeture, sans impact).",
            file=sys.stderr,
        )
    return pdfs


def page_count(pdf: Path) -> int:
    qpdf = find_tool("QPDF", config.QPDF_CANDIDATES)
    result = _run([qpdf, "--show-npages", str(pdf)], capture_output=True, text=True)
    if result.returncode != 0:
        raise RenduError(f"qpdf ne peut pas lire {pdf} : {result.stderr.strip()}")
    return int(result.stdout.strip())


def overflow_warnings(pdfs: list[Path], labels: list[str]) -> list[str]:
    """Une leçon doit tenir sur une page : signale celles qui débordent."""
    warnings = []
    for pdf, label in zip(pdfs, labels, strict=True):
        n = page_count(pdf)
        if n != 1:
            warnings.append(f"Attention : la leçon {label} déborde ({n} pages au lieu de 1) : raccourcir des lignes.")
    return warnings


def merge_pdfs(pdfs: list[Path], output: Path) -> None:
    qpdf = find_tool("QPDF", config.QPDF_CANDIDATES)
    result = _run([qpdf, "--empty", "--pages", *map(str, pdfs), "--", str(output)], capture_output=True, text=True)
    if result.returncode != 0:
        raise RenduError(f"qpdf n'a pas pu fusionner les pages (code {result.returncode}) : {result.stderr.strip()}")
