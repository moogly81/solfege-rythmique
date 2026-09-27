"""Étape 2 : symboles rythmiques, validation des mesures, ligatures.

1 temps (noire) = 12 divisions : divisible par 3 (triolets) et par 4 (doubles).
"""

from typing import NamedTuple

from .cahier import Cahier, Exercise, SourceLine
from .erreurs import CahierError

DIVISIONS = 12  # divisions MusicXML par noire
BEAT = DIVISIONS


class Token(NamedTuple):
    duration: int | None  # en divisions ; None = mesure entière
    kind: str  # type MusicXML
    is_rest: bool
    dotted: bool


TOKENS = {
    "r": Token(48, "whole", False, False),
    "b.": Token(36, "half", False, True),
    "b": Token(24, "half", False, False),
    "n.": Token(18, "quarter", False, True),
    "n": Token(12, "quarter", False, False),
    "c.": Token(9, "eighth", False, True),
    "c": Token(6, "eighth", False, False),
    "t": Token(4, "eighth", False, False),  # croche de triolet (3 dans 1 temps)
    "d": Token(3, "16th", False, False),
    "p": Token(None, "whole", True, False),  # durée = mesure entière
    "dp": Token(24, "half", True, False),
    "s": Token(12, "quarter", True, False),
    "ds": Token(6, "eighth", True, False),
}
BEAM_LEVELS = {"eighth": 1, "16th": 2}

Measure = list[str]


def duration(token: str, measure_len: int) -> int:
    dur = TOKENS[token].duration
    return measure_len if dur is None else dur


def parse_time(time_sig: str, where: str) -> int:
    """« 3/4 » -> 3 (nombre de temps)."""
    try:
        beats, beat_type = (int(x) for x in time_sig.split("/"))
    except ValueError:
        raise CahierError(f"{where} : chiffrage invalide « {time_sig} »") from None
    if beat_type != 4:
        raise CahierError(f"{where} : seuls les chiffrages en /4 sont gérés ({time_sig})")
    return beats


def parse_line(line: str, beats: int, where: str) -> list[Measure]:
    """Découpe une ligne en mesures et vérifie symboles, durées et triolets."""
    measure_len = beats * BEAT
    measures = []
    for m_idx, chunk in enumerate(line.split("|"), start=1):
        here = f"{where}, mesure {m_idx} ({chunk.strip()})"
        tokens = chunk.split()
        for t in tokens:
            if t not in TOKENS:
                raise CahierError(f"{here} : symbole inconnu « {t} »")
        if "p" in tokens and tokens != ["p"]:
            raise CahierError(f"{here} : la pause « p » doit être seule dans sa mesure")
        # Triolets : groupes de 3 « t » commençant sur un temps
        pos, i = 0, 0
        while i < len(tokens):
            if tokens[i] == "t":
                if pos % BEAT or tokens[i : i + 3] != ["t"] * 3:
                    raise CahierError(f"{here} : un triolet = 3 « t » au début d'un temps")
                pos, i = pos + BEAT, i + 3
            else:
                pos, i = pos + duration(tokens[i], measure_len), i + 1
        if pos != measure_len:
            raise CahierError(f"{here} : {pos / BEAT:g} temps au lieu de {beats}")
        measures.append(tokens)
    return measures


def parse_syllables(syllables: str, measures: list[Measure], where: str) -> list[list[str]]:
    """« qua- tre dou- bles | 1 2 » -> syllabes de chaque mesure, une par note (silences exclus)."""
    chunks = syllables.split("|")
    if len(chunks) != len(measures):
        raise CahierError(f"{where} : {len(chunks)} mesures de syllabes pour {len(measures)} mesures de rythme")
    result = []
    for m_idx, (chunk, tokens) in enumerate(zip(chunks, measures, strict=True), start=1):
        sylls = chunk.split()
        n_notes = sum(not TOKENS[t].is_rest for t in tokens)
        if len(sylls) != n_notes:
            raise CahierError(f"{where}, mesure {m_idx} ({chunk.strip()}) : {len(sylls)} syllabes pour {n_notes} notes")
        result.append(sylls)
    return result


class ParsedLine(NamedTuple):
    measures: list[Measure]
    syllables: list[list[str]] | None


def _parse_source_line(line: SourceLine, beats: int, number: str) -> ParsedLine:
    measures = parse_line(line.text, beats, f"{line.where} (exercice {number})")
    if line.syllables is None:
        return ParsedLine(measures, None)
    where = f"{line.syllables_where} (syllabes de l'exercice {number})"
    return ParsedLine(measures, parse_syllables(line.syllables, measures, where))


def parse_exercise(exercise: Exercise) -> tuple[int, list[ParsedLine]]:
    """-> (nombre de temps, mesures et syllabes de chaque ligne)."""
    beats = parse_time(exercise.time, exercise.where)
    return beats, [_parse_source_line(line, beats, exercise.number) for line in exercise.lines]


def check(cahier: Cahier) -> list[str]:
    """Vérifie tous les exercices ; renvoie toutes les erreurs (au plus une par ligne)."""
    errors = []
    for _, lesson in cahier.lessons():
        for exercise in lesson.exercises:
            try:
                beats = parse_time(exercise.time, exercise.where)
            except CahierError as e:
                errors.append(str(e))
                continue
            for line in exercise.lines:
                try:
                    _parse_source_line(line, beats, exercise.number)
                except CahierError as e:
                    errors.append(str(e))
    return errors


def compute_beams(tokens: Measure) -> list[dict[int, str]]:
    """Pour chaque note de la mesure : {niveau: valeur} de ligatures MusicXML
    (begin/continue/end/forward hook/backward hook). Groupes = par temps."""
    beams: list[dict[int, str]] = [{} for _ in tokens]
    groups, current, current_beat, pos = [], [], -1, 0
    for i, t in enumerate(tokens):
        tok = TOKENS[t]
        beamable = tok.kind in BEAM_LEVELS and not tok.is_rest
        if beamable and current and pos // BEAT == current_beat:
            current.append(i)
        else:
            if len(current) > 1:
                groups.append(current)
            current = [i] if beamable else []
            current_beat = pos // BEAT
        pos += tok.duration or 0
    if len(current) > 1:
        groups.append(current)

    for g in groups:
        for k, i in enumerate(g):
            beams[i][1] = "begin" if k == 0 else "end" if k == len(g) - 1 else "continue"
        # 2e barre : sur les suites de doubles-croches consécutives
        k = 0
        while k < len(g):
            if TOKENS[tokens[g[k]]].kind != "16th":
                k += 1
                continue
            run = [g[k]]
            while k + 1 < len(g) and TOKENS[tokens[g[k + 1]]].kind == "16th":
                k += 1
                run.append(g[k])
            if len(run) == 1:
                beams[run[0]][2] = "backward hook" if run[0] == g[-1] else "forward hook"
            else:
                for j, i in enumerate(run):
                    beams[i][2] = "begin" if j == 0 else "end" if j == len(run) - 1 else "continue"
            k += 1
    return beams
