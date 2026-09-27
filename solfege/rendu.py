"""Étape 4 : MusicXML -> PDF (MuseScore 4) puis fusion des pages (qpdf)."""

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import config
from .erreurs import RenduError


def find_tool(env_var: str, candidates: list[str]) -> str:
    for c in [os.environ.get(env_var), *candidates]:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    raise RenduError(f"Outil introuvable ({env_var}). Installez-le ou définissez la variable {env_var}.")


def render_pdfs(xml_paths: list[Path], build_dir: Path) -> list[Path]:
    """Exporte chaque MusicXML en PDF, en un seul appel MuseScore (job JSON)."""
    mscore = find_tool("MSCORE", config.MSCORE_CANDIDATES)
    for old in build_dir.glob("page_*.pdf"):
        old.unlink()  # évite de fusionner des pages d'une version plus longue
    pdfs = [p.with_suffix(".pdf") for p in xml_paths]
    jobs = [{"in": str(x.resolve()), "out": str(p.resolve())} for x, p in zip(xml_paths, pdfs, strict=True)]

    style_file = build_dir / "style.mss"
    style_file.write_text(config.STYLE_MSS)
    job_file = build_dir / "job.json"
    job_file.write_text(json.dumps(jobs, indent=2))
    # MuseScore 4.7 peut avorter (SIGABRT, "mutex lock failed") dans exit(),
    # APRÈS avoir écrit les PDF : bug de destruction des statiques côté
    # MuseScore. On juge donc le résultat sur les fichiers, pas le code retour.
    log_file = build_dir / "mscore.log"
    with log_file.open("w") as log:
        rc = subprocess.run(
            [mscore, "-S", str(style_file.resolve()), "-j", str(job_file)],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        ).returncode
    missing = [str(p) for p in pdfs if not p.exists()]
    if missing:
        raise RenduError(f"MuseScore n'a pas produit : {', '.join(missing)} (voir {log_file})")
    if rc != 0:
        print(f"Note : MuseScore a quitté avec le code {rc} après export (bug connu à la fermeture, sans impact).")
    return pdfs


def merge_pdfs(pdfs: list[Path], output: Path) -> None:
    qpdf = find_tool("QPDF", config.QPDF_CANDIDATES)
    subprocess.run([qpdf, "--empty", "--pages", *map(str, pdfs), "--", str(output)], check=True)
