"""Cahier de lecture rythmique : cahier.txt -> LilyPond -> PDF.

Étapes, une par module :
  cahier    lecture de cahier.txt -> modèle (chapitres, leçons, exercices)
  rythme    symboles, validation des mesures, ligatures
  lilypond  le cahier -> un seul document .ly, une page par leçon (fonction pure)
  rendu     .ly -> PDF (LilyPond), leçons qui débordent
  cli       enchaîne les étapes (python3 -m solfege)
"""

__version__ = "0.3.0"
