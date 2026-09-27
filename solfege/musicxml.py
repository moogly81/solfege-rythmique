"""Étape 3 : une leçon -> un document MusicXML (une page). Fonction pure."""

from xml.sax.saxutils import escape

from . import config
from .cahier import Chapter, Lesson
from .rythme import BEAT, DIVISIONS, TOKENS, compute_beams, duration, parse_exercise


def syllabic(prev: str | None, syll: str) -> str:
    """Position MusicXML d'une syllabe : « qua- tre » -> begin, end."""
    continues, continued = syll.endswith("-"), bool(prev and prev.endswith("-"))
    if continues:
        return "middle" if continued else "begin"
    return "end" if continued else "single"


def lyric_xml(prev: str | None, syll: str) -> str:
    text = escape((syll.removesuffix("-") if len(syll) > 1 else syll).replace("_", " "))  # « ron-de_lon-gue »
    return f'<lyric number="1"><syllabic>{syllabic(prev, syll)}</syllabic><text>{text}</text></lyric>'


def note_xml(token: str, beams: dict[int, str], measure_len: int, pos: int, lyric: str = "") -> str:
    _, kind, is_rest, dotted = TOKENS[token]
    out = ["<note>"]
    if is_rest:
        out.append('<rest measure="yes"/>' if token == "p" else "<rest/>")
    else:
        out.append("<unpitched><display-step>B</display-step><display-octave>4</display-octave></unpitched>")
    out.append(f"<duration>{duration(token, measure_len)}</duration>")
    if not is_rest:
        out.append('<instrument id="P1-I1"/>')
    out.append(f"<voice>1</voice><type>{kind}</type>")
    if dotted:
        out.append("<dot/>")
    if token == "t":
        out.append(
            "<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>"
        )
    if not is_rest and kind != "whole":
        out.append("<stem>up</stem>")
    for level in sorted(beams):
        out.append(f'<beam number="{level}">{beams[level]}</beam>')
    if token == "t" and pos % BEAT in (0, 2 * BEAT // 3):
        kind_tuplet = "start" if pos % BEAT == 0 else "stop"
        out.append(f'<notations><tuplet type="{kind_tuplet}" number="1" bracket="no"/></notations>')
    out.append(lyric)
    out.append("</note>")
    return "".join(out)


def _measures_xml(lesson: Lesson) -> list[str]:
    measures_xml, number = [], 0
    for exercise in lesson.exercises:
        beats, parsed = parse_exercise(exercise)
        measure_len = beats * BEAT
        prev_syll = None
        for line_idx, (measures, syllables) in enumerate(parsed):
            for m_idx, tokens in enumerate(measures):
                sylls = iter(syllables[m_idx]) if syllables else None
                number += 1
                parts = [f'<measure number="{number}">']
                if m_idx == 0 and number > 1:
                    parts.append('<print new-system="yes"/>')
                if line_idx == 0 and m_idx == 0:
                    # Début d'exercice : chiffrage (ré)affiché + repère encadré N.M.K
                    attrs = ""
                    if number == 1:
                        attrs += f'<divisions>{DIVISIONS}</divisions><key print-object="no"><fifths>0</fifths></key>'
                    attrs += f"<time><beats>{beats}</beats><beat-type>4</beat-type></time>"
                    if number == 1:
                        attrs += (
                            "<staff-details><staff-lines>1</staff-lines></staff-details>"
                            "<clef><sign>percussion</sign></clef>"
                        )
                    parts.append(f"<attributes>{attrs}</attributes>")
                    parts.append(
                        '<direction placement="above"><direction-type>'
                        f'<rehearsal enclosure="rectangle">{exercise.number}</rehearsal>'
                        "</direction-type></direction>"
                    )
                pos = 0
                for t, b in zip(tokens, compute_beams(tokens), strict=True):
                    lyric = ""
                    if sylls is not None and not TOKENS[t].is_rest:
                        syll = next(sylls)
                        lyric, prev_syll = lyric_xml(prev_syll, syll), syll
                    parts.append(note_xml(t, b, measure_len, pos, lyric))
                    pos += duration(t, measure_len)
                if line_idx == len(parsed) - 1 and m_idx == len(measures) - 1:
                    parts.append('<barline location="right"><bar-style>light-heavy</bar-style></barline>')
                parts.append("</measure>")
                measures_xml.append("".join(parts))
    return measures_xml


def lesson_to_musicxml(chapter: Chapter, lesson: Lesson) -> str:
    tenths_per_mm = 40 / config.STAFF_SIZE_MM
    pw, ph = config.PAGE_W_MM * tenths_per_mm, config.PAGE_H_MM * tenths_per_mm
    mg = config.MARGIN_MM * tenths_per_mm
    measures_xml = _measures_xml(lesson)

    chap = escape(f"Chapitre {chapter.number} · {chapter.title}")
    title = escape(f"{lesson.number}  {lesson.title}")
    instr = escape(lesson.instruction)
    # En-tête = un seul texte sur 3 lignes (chapitre / titre / consigne) :
    # MuseScore empile mal plusieurs credits distincts (chevauchements).
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="4.0">
  <work><work-title>{title}</work-title></work>
  <defaults>
    <scaling><millimeters>{config.STAFF_SIZE_MM}</millimeters><tenths>40</tenths></scaling>
    <page-layout>
      <page-height>{ph:.0f}</page-height><page-width>{pw:.0f}</page-width>
      <page-margins type="both"><left-margin>{mg:.0f}</left-margin><right-margin>{mg:.0f}</right-margin>
      <top-margin>{mg:.0f}</top-margin><bottom-margin>{mg:.0f}</bottom-margin></page-margins>
    </page-layout>
    <system-layout><system-distance>{config.SYSTEM_DISTANCE}</system-distance><top-system-distance>150</top-system-distance></system-layout>
  </defaults>
  <credit page="1"><credit-type>title</credit-type>
    <credit-words justify="center" halign="center" valign="top" default-x="{pw / 2:.0f}" default-y="{ph - mg:.0f}" font-size="12" font-weight="normal">{chap}&#10;</credit-words><credit-words font-size="22" font-weight="bold">{title}&#10;</credit-words><credit-words font-size="13" font-weight="normal" font-style="italic">{instr}</credit-words></credit>
  <part-list><score-part id="P1"><part-name print-object="no">Rythme</part-name>
    <score-instrument id="P1-I1"><instrument-name>Hand Clap</instrument-name></score-instrument>
    <midi-instrument id="P1-I1"><midi-channel>10</midi-channel><midi-unpitched>40</midi-unpitched></midi-instrument>
  </score-part></part-list>
  <part id="P1">
{chr(10).join(measures_xml)}
  </part>
</score-partwise>
"""
