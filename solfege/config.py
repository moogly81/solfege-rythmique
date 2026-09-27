"""Réglages : chemins par défaut et mise en page."""

from pathlib import Path

CAHIER_FILE = Path("cahier.txt")
BUILD_DIR = Path("build")
OUTPUT_PDF = Path("cahier_rythme.pdf")
DEFAULT_TIME = "4/4"

MSCORE_CANDIDATES = ["/Applications/MuseScore 4.app/Contents/MacOS/mscore", "mscore", "musescore"]
QPDF_CANDIDATES = ["qpdf", "/opt/homebrew/bin/qpdf"]

# Taille de la gravure : hauteur (mm) d'un "espace de portée" x4.
# Plus grand = notes plus grosses. 7 mm ~ standard, 9 mm ~ confortable enfant.
STAFF_SIZE_MM = 8.5
# Écart vertical entre deux lignes (en dixièmes, 40 = hauteur d'une portée).
SYSTEM_DISTANCE = 140
PAGE_W_MM, PAGE_H_MM = 210, 297
MARGIN_MM = 15

# Style MuseScore appliqué à toutes les pages (clés = réglages MuseScore 4).
# Distances en "espaces" (sp) ; 1 sp = STAFF_SIZE_MM / 4.
STYLE_MSS = f"""<?xml version="1.0" encoding="UTF-8"?>
<museScore version="4.70"><Style>
  <spatium>{STAFF_SIZE_MM / 4}</spatium>
  <showMeasureNumber>0</showMeasureNumber>
  <minSystemDistance>9</minSystemDistance>
  <maxSystemDistance>30</maxSystemDistance>
  <enableVerticalSpread>1</enableVerticalSpread>
  <minMeasureWidth>6</minMeasureWidth>
  <lastSystemFillLimit>0</lastSystemFillLimit>
  <genCourtesyTimesig>0</genCourtesyTimesig>
  <lyricsMinDistance>1.2</lyricsMinDistance>
  <lyricsDashForce>1</lyricsDashForce>
</Style></museScore>
"""
