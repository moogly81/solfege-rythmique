"""Étape 3 (LilyPond) : une leçon -> un document .ly (une page). Fonction pure."""

from . import config
from .cahier import Chapter, Lesson
from .rythme import TOKENS, beam_groups, parse_exercise

KIND_DUR = {"whole": "1", "half": "2", "quarter": "4", "eighth": "8", "16th": "16"}
# Pause « p » (silence = toute la mesure) : durée LilyPond selon le nombre de temps.
# Au-delà de 4 temps (hors usage réel, cf. NOTATION.md) : repli sur la ronde, non testé visuellement.
FULL_REST = {1: "4", 2: "2", 3: "2.", 4: "1"}


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _plain_duration(token: str, beats: int) -> str:
    """Durée LilyPond du token (hors pause « p », qui dépend du chiffrage)."""
    if token == "p":
        return FULL_REST.get(beats, "1")
    _, kind, _, dotted = TOKENS[token]
    return KIND_DUR[kind] + ("." if dotted else "")


def _atom(token: str, beats: int) -> str:
    """Un token -> son atome LilyPond : hauteur fixe « b » (seule à tomber sur l'unique ligne
    de la portée réduite à 1 ligne, avec la clé de percussion — vérifié par rendu réel),
    « r » pour les silences ordinaires, « R » (repos de mesure) pour la pause."""
    is_rest = TOKENS[token].is_rest
    dur = _plain_duration(token, beats)
    if token == "p":
        return f"R{dur}"
    return f"{'r' if is_rest else 'b'}{dur}"


def _lyric_word(syll: str) -> str:
    """« qua- » -> « qua -- » (continuation) ; « ron-de_lon-gue » -> une syllabe entre guillemets (espace visible) ;
    un mot tout en chiffres (compte de temps « 1 », « 2 »...) entre guillemets aussi : LilyPond lirait sinon
    un nombre isolé comme la durée du mot précédent, pas comme un nouveau mot."""
    if syll.endswith("-"):
        return f"{_escape(syll[:-1])} --"
    if "_" in syll or " " in syll or syll.isdigit():
        return f'"{_escape(syll.replace("_", " "))}"'
    return _escape(syll)


def _measure_music(tokens: list[str], beats: int) -> str:
    """Notes/silences d'une mesure, avec crochets de ligature « [ ]  » et triolets."""
    groups = beam_groups(tokens)
    starts = {g[0] for g in groups}
    ends = {g[-1] for g in groups}

    def bracketed(i: int, atom: str) -> str:
        if i in starts:
            atom += "["
        if i in ends:
            atom += "]"
        return atom

    atoms, i = [], 0
    while i < len(tokens):
        if tokens[i] == "t":
            trio = " ".join(bracketed(i + k, _atom(t, beats)) for k, t in enumerate(tokens[i : i + 3]))
            atoms.append(r"\once \override TupletBracket.bracket-visibility = ##f \tuplet 3/2 { " + trio + " }")
            i += 3
            continue
        atoms.append(bracketed(i, _atom(tokens[i], beats)))
        i += 1
    return " ".join(atoms)


def _measure_lyrics(tokens: list[str], sylls: list[str | None], beats: int) -> str:
    """Paroles d'une mesure : une syllabe par note/silence chuchoté, "\\skip" ailleurs
    (les silences ne « mangent » pas de syllabe par défaut sous LilyPond)."""
    words = []
    for token, syll in zip(tokens, sylls, strict=True):
        words.append(_lyric_word(syll) if syll is not None else f"\\skip {_plain_duration(token, beats)}")
    return " ".join(words)


def _body(lesson: Lesson) -> tuple[str, str]:
    music_lines, lyric_lines = [], []
    prev_time = None
    first_source_line = True
    for exercise in lesson.exercises:
        beats, parsed = parse_exercise(exercise)
        for line_idx, (measures, syllables) in enumerate(parsed):
            if not first_source_line:
                music_lines.append(r"\break")
            first_source_line = False
            has_syllables = syllables is not None
            for m_idx, tokens in enumerate(measures):
                sylls = syllables[m_idx] if has_syllables else [None] * len(tokens)
                if line_idx == 0 and m_idx == 0:
                    if exercise.time != prev_time:
                        music_lines.append(rf"\time {exercise.time}")
                        prev_time = exercise.time
                    music_lines.append(rf'\mark \markup {{ \box "{exercise.number}" }}')
                music_lines.append(_measure_music(tokens, beats))
                if line_idx == len(parsed) - 1 and m_idx == len(measures) - 1:
                    music_lines.append(r'\bar "|."')
                music_lines.append("|")
                if has_syllables:
                    lyric_lines.append(_measure_lyrics(tokens, sylls, beats))
                else:
                    lyric_lines.append(" ".join(f"\\skip {_plain_duration(t, beats)}" for t in tokens))
    return " ".join(music_lines), " ".join(lyric_lines)


def lesson_to_lilypond(chapter: Chapter, lesson: Lesson) -> str:
    music, lyrics = _body(lesson)
    chap = _escape(f"Chapitre {chapter.number} · {chapter.title}")
    title = _escape(f"{lesson.number}  {lesson.title}")
    instr = _escape(lesson.instruction)

    staff_size_pt = config.STAFF_SIZE_MM * 72 / 25.4
    return f"""\\version "2.24.0"
#(set-global-staff-size {staff_size_pt:.2f})

\\paper {{
  #(set-paper-size "a4")
  top-margin = {config.MARGIN_MM}\\mm
  bottom-margin = {config.MARGIN_MM}\\mm
  left-margin = {config.MARGIN_MM}\\mm
  right-margin = {config.MARGIN_MM}\\mm
  indent = 0
  ragged-last-bottom = ##f
  print-page-number = ##f
  system-system-spacing.basic-distance = {config.SYSTEM_DISTANCE / 10}
  markup-system-spacing.basic-distance = {config.TOP_SYSTEM_DISTANCE / 10}
}}

\\header {{
  tagline = ##f
}}

rythme = {{
  \\autoBeamOff
  \\override Staff.StaffSymbol.line-count = #1
  \\override Stem.direction = #UP
  \\clef "percussion"
  {music}
}}

paroles = \\lyricmode {{
  {lyrics}
}}

\\book {{
  \\markup \\fill-line {{
    \\center-column {{
      \\abs-fontsize #{config.CHAPTER_PT} "{chap}"
      \\abs-fontsize #{config.TITLE_PT} \\bold "{title}"
      \\abs-fontsize #{config.INSTRUCTION_PT} \\italic "{instr}"
    }}
  }}
  \\score {{
    <<
      \\new Staff \\new Voice = "rythme" \\rythme
      \\addlyrics \\paroles
    >>
    \\layout {{
      \\context {{ \\Score \\remove "Bar_number_engraver" }}
    }}
  }}
}}
"""
