"""Étape 3 (LilyPond) : le cahier -> un seul document .ly, une page (\\bookpart) par leçon. Fonctions pures."""

from . import config
from .cahier import Cahier, Chapter, Lesson
from .rythme import TOKENS, beam_groups, parse_exercise

# Pause « p » (silence = toute la mesure) : durée LilyPond selon le nombre de temps.
# Au-delà de 4 temps (hors usage réel, cf. NOTATION.md) : repli sur la ronde, non testé visuellement.
FULL_REST = {1: "4", 2: "2", 3: "2.", 4: "1"}


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _plain_duration(token: str, beats: int) -> str:
    """Durée LilyPond du token (hors pause « p », qui dépend du chiffrage)."""
    if token == "p":
        return FULL_REST.get(beats, "1")
    return TOKENS[token].ly


PITCH = "c'"  # seule hauteur à tomber exactement au milieu de l'unique ligne (clé de percussion,
# portée réduite à 1 ligne) — vérifié par rendu réel : « b » (sans marque d'octave, donc B3)
# tombe dans l'espace juste en dessous de la ligne, pas dessus.


def _atom(token: str, beats: int) -> str:
    """Un token -> son atome LilyPond : hauteur fixe PITCH pour une note, « r » pour un silence
    ordinaire, « R » (repos de mesure) pour la pause."""
    is_rest = TOKENS[token].is_rest
    dur = _plain_duration(token, beats)
    if token == "p":
        return f"R{dur}"
    return f"r{dur}" if is_rest else f"{PITCH}{dur}"


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


def _measure_hidden(tokens: list[str], beats: int) -> str:
    """Même rythme qu'une mesure de « _measure_music », mais toujours en notes (jamais de silence) :
    sert de piste invisible (« NullVoice ») pour aligner les paroles. Nécessaire parce que
    \\addlyrics/\\lyricsto saute toujours silencieusement un silence, même écrit en note suivie de
    « \\rest » — vérifié par rendu réel : aucune syllabe ne s'attache jamais à un silence si les
    paroles suivent directement la portée imprimée. Une piste jumelle où chaque temps, silences
    compris, est une vraie note contourne le problème : \\lyricsto s'y accroche alors normalement,
    y compris pour chuchoter une syllabe sur ce qui est un silence à l'écran."""
    atoms, i = [], 0
    while i < len(tokens):
        if tokens[i] == "t":
            trio = " ".join(f"{PITCH}{_plain_duration(t, beats)}" for t in tokens[i : i + 3])
            atoms.append(r"\tuplet 3/2 { " + trio + " }")
            i += 3
            continue
        atoms.append(f"{PITCH}{_plain_duration(tokens[i], beats)}")
        i += 1
    return " ".join(atoms)


def _measure_lyrics(tokens: list[str], sylls: list[str | None], beats: int) -> str:
    """Paroles d'une mesure : une syllabe par note ou silence chuchoté, "\\skip" ailleurs — aligné
    sur la piste invisible (« _measure_hidden »), où chaque token, silence compris, est une note."""
    words = []
    for token, syll in zip(tokens, sylls, strict=True):
        words.append(_lyric_word(syll) if syll is not None else f"\\skip {_plain_duration(token, beats)}")
    return " ".join(words)


def _body(lesson: Lesson) -> tuple[str, str, str]:
    music_lines, hidden_lines, lyric_lines = [], [], []
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
                hidden_lines.append(_measure_hidden(tokens, beats))
                lyric_lines.append(_measure_lyrics(tokens, sylls, beats))
    return " ".join(music_lines), " ".join(hidden_lines), " ".join(lyric_lines)


PAGES_MARKER = "solfege-pages"  # ligne écrite dans le journal LilyPond : « solfege-pages 4.3 2 » = leçon 4.3, 2 pages


def lesson_to_lilypond(chapter: Chapter, lesson: Lesson) -> str:
    """Une leçon -> ses variables (« rythme », « cachee », « paroles ») et son \\bookpart (= une nouvelle page).
    Les variables sont redéfinies avant chaque \\bookpart : LilyPond copie leur valeur à la lecture.
    « page-post-process » écrit dans le journal le nombre de pages de la leçon (détection des débordements)."""
    music, hidden, lyrics = _body(lesson)
    chap = _escape(f"Chapitre {chapter.number} · {chapter.title}")
    title = _escape(f"{lesson.number}  {lesson.title}")
    instr = _escape(lesson.instruction)
    return f"""
rythme = {{
  \\autoBeamOff
  \\numericTimeSignature
  \\override Staff.StaffSymbol.line-count = #1
  \\override Stem.direction = #UP
  \\clef "percussion"
  {music}
}}

cachee = {{
  {hidden}
}}

paroles = \\lyricmode {{
  {lyrics}
}}

\\bookpart {{
  \\paper {{
    #(define (page-post-process layout pages) (ly:message "{PAGES_MARKER} {lesson.number} ~a" (length pages)))
  }}
  \\markup \\fill-line {{
    \\center-column {{
      \\abs-fontsize #{config.CHAPTER_PT} "{chap}"
      \\abs-fontsize #{config.TITLE_PT} \\bold "{title}"
      \\abs-fontsize #{config.INSTRUCTION_PT} \\italic "{instr}"
    }}
  }}
  \\score {{
    <<
      \\new Staff <<
        \\new Voice = "rythme" \\rythme
        \\new NullVoice = "cachee" \\cachee
      >>
      \\new Lyrics \\lyricsto "cachee" \\paroles
    >>
  }}
}}
"""


def cahier_to_lilypond(cahier: Cahier) -> str:
    """Tout le cahier -> un seul document .ly : réglages communs, puis une page (\\bookpart) par leçon."""
    staff_size_pt = config.STAFF_SIZE_MM * 72 / 25.4
    preamble = f"""\\version "2.24.0"
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
  system-system-spacing.basic-distance = {config.SYSTEM_DISTANCE}
  markup-system-spacing.basic-distance = {config.TOP_SYSTEM_DISTANCE}
}}

\\header {{
  tagline = ##f
}}

\\layout {{
  \\context {{
    \\Score
    \\remove "Bar_number_engraver"
    \\override TimeSignature.break-visibility = #end-of-line-invisible
  }}
}}
"""
    return preamble + "".join(lesson_to_lilypond(chapter, lesson) for chapter, lesson in cahier.lessons())
