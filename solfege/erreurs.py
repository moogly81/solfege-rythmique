"""Erreurs affichées à l'utilisateur (non technicien) : messages en français."""


class SolfegeError(Exception):
    """Erreur attendue : le message suffit, pas de trace Python."""


class CahierError(SolfegeError):
    """Contenu de cahier.txt invalide (structure ou rythme)."""


class RenduError(SolfegeError):
    """Outil externe absent ou export raté."""
