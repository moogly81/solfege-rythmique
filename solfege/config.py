"""Réglages : chemins par défaut et mise en page."""

from pathlib import Path

CAHIER_FILE = Path("cahier.txt")
BUILD_DIR = Path("build")
OUTPUT_PDF = Path("cahier_rythme.pdf")
DEFAULT_TIME = "4/4"

LILYPOND_CANDIDATES = ["lilypond", "/opt/homebrew/bin/lilypond"]

# Taille de la gravure : hauteur (mm) d'un "espace de portée" x4.
# Plus grand = notes plus grosses. 7 mm ~ standard, 9 mm ~ confortable enfant.
STAFF_SIZE_MM = 8.5
# Écart vertical entre deux lignes, en espaces de portée LilyPond (4 = hauteur d'une portée à 5 lignes).
SYSTEM_DISTANCE = 14.0
# Distance entre l'en-tête (3 lignes de texte) et la 1re ligne de musique (espaces de portée).
TOP_SYSTEM_DISTANCE = 15.0
# Tailles (points) des 3 lignes de l'en-tête : chapitre (romain), titre (gras), consigne (italique).
CHAPTER_PT, TITLE_PT, INSTRUCTION_PT = 12, 22, 13
PAGE_W_MM, PAGE_H_MM = 210, 297
MARGIN_MM = 15
