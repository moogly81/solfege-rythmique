"""Cahier de lecture rythmique : cahier.txt -> MusicXML -> PDF (MuseScore 4).

Étapes, une par module :
  cahier    lecture de cahier.txt -> modèle (chapitres, leçons, exercices)
  rythme    symboles, validation des mesures, ligatures
  musicxml  une leçon -> un document MusicXML (fonction pure)
  rendu     MusicXML -> PDF (MuseScore) puis fusion (qpdf)
  cli       enchaîne les étapes (python3 -m solfege)
"""

__version__ = "0.2.0"
