"""Enchaîne les étapes : lecture -> vérification -> MusicXML -> PDF.

python3 -m solfege          tout (PDF)
python3 -m solfege check    vérifie cahier.txt seulement (rapide, sans MuseScore)
python3 -m solfege xml      vérifie + écrit les MusicXML dans build/

Codes de retour : 0 ok ; 1 erreur (message sur stderr) ; 2 PDF produit mais une leçon déborde.
"""

import argparse
import sys
from pathlib import Path

from . import config
from .cahier import Cahier, load_cahier
from .erreurs import CahierError, SolfegeError
from .musicxml import lesson_to_musicxml
from .rendu import merge_pdfs, overflow_warnings, render_pdfs
from .rythme import check


def load_and_check(path: Path) -> Cahier:
    cahier = load_cahier(path)
    errors = check(cahier)
    if errors:
        raise CahierError("\n".join(errors))
    return cahier


def write_xml(cahier: Cahier, build_dir: Path) -> list[Path]:
    build_dir.mkdir(parents=True, exist_ok=True)
    for old in build_dir.glob("page_*.musicxml"):
        old.unlink()
    paths = []
    for page_no, (chapter, lesson) in enumerate(cahier.lessons(), start=1):
        path = build_dir / f"page_{page_no:02d}.musicxml"
        path.write_text(lesson_to_musicxml(chapter, lesson), encoding="utf-8")
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="solfege", description="Cahier de lecture rythmique")
    parser.add_argument(
        "step", nargs="?", default="pdf", choices=["check", "xml", "pdf"], help="étape finale (défaut : pdf)"
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
        xml_paths = write_xml(cahier, args.build)
        if args.step == "xml":
            print(f"MusicXML écrits dans {args.build}/ ({len(xml_paths)} pages)")
            return 0
        pdfs = render_pdfs(xml_paths, args.build)
        warnings = overflow_warnings(pdfs, [lesson.number for _, lesson in cahier.lessons()])
        for w in warnings:
            print(w, file=sys.stderr)
        merge_pdfs(pdfs, args.output)
        print(f"PDF généré : {args.output} ({len(xml_paths)} pages)")
        return 2 if warnings else 0
    except SolfegeError as e:
        print(e, file=sys.stderr)
        return 1
