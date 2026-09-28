"""Enchaîne les étapes : lecture -> vérification -> LilyPond -> PDF.

python3 -m solfege          tout (PDF)
python3 -m solfege check    vérifie cahier.txt seulement (rapide, sans LilyPond)
python3 -m solfege ly       vérifie + écrit build/cahier.ly

Codes de retour : 0 ok ; 1 erreur (message sur stderr) ; 2 PDF produit mais une leçon déborde.
"""

import argparse
import shutil
import sys
from pathlib import Path

from . import config
from .cahier import Cahier, load_cahier
from .erreurs import CahierError, SolfegeError
from .lilypond import cahier_to_lilypond
from .rendu import overflow_warnings, render_pdf
from .rythme import check


def load_and_check(path: Path) -> Cahier:
    cahier = load_cahier(path)
    errors = check(cahier)
    if errors:
        raise CahierError("\n".join(errors))
    return cahier


def write_ly(cahier: Cahier, build_dir: Path) -> Path:
    build_dir.mkdir(parents=True, exist_ok=True)
    for old in build_dir.glob("page_*.ly"):
        old.unlink()  # restes de l'ancien rendu page par page
    path = build_dir / "cahier.ly"
    path.write_text(cahier_to_lilypond(cahier), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="solfege", description="Cahier de lecture rythmique")
    parser.add_argument(
        "step", nargs="?", default="pdf", choices=["check", "ly", "pdf"], help="étape finale (défaut : pdf)"
    )
    parser.add_argument("--cahier", type=Path, default=config.CAHIER_FILE)
    parser.add_argument("--build", type=Path, default=config.BUILD_DIR)
    parser.add_argument("--output", type=Path, default=config.OUTPUT_PDF)
    args = parser.parse_args(argv)

    try:
        cahier = load_and_check(args.cahier)
        n_lessons = sum(1 for _ in cahier.lessons())
        if args.step == "check":
            print(f"{args.cahier} : OK ({len(cahier.chapters)} chapitres, {n_lessons} leçons)")
            return 0
        ly_path = write_ly(cahier, args.build)
        if args.step == "ly":
            print(f"LilyPond écrit : {ly_path} ({n_lessons} pages)")
            return 0
        pdf, pages = render_pdf(ly_path, args.build)
        warnings = overflow_warnings(pages, [lesson.number for _, lesson in cahier.lessons()])
        for w in warnings:
            print(w, file=sys.stderr)
        shutil.copyfile(pdf, args.output)
        print(f"PDF généré : {args.output} ({sum(pages.values())} pages)")
        return 2 if warnings else 0
    except SolfegeError as e:
        print(e, file=sys.stderr)
        return 1
