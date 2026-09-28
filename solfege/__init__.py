"""Cahier de lecture rythmique : cahier.txt -> LilyPond -> PDF.

Étapes, une par module :
  cahier    lecture de cahier.txt -> modèle (chapitres, leçons, exercices)
  rythme    symboles, validation des mesures, ligatures
  lilypond  une leçon -> un document .ly (fonction pure)
  rendu     .ly -> PDF (LilyPond) puis fusion (qpdf)
  cli       enchaîne les étapes (python3 -m solfege)
"""

__version__ = "0.3.0"
