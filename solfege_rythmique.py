#!/usr/bin/env python3
"""
Cahier de lecture rythmique (ligne rythmique unique, 2/4, 3/4, 4/4).

Pipeline : contenu (cahier.txt) -> un fichier MusicXML par page -> PDF via
MuseScore 4 (gravure pro, police Leland) -> fusion des pages avec qpdf.

Pour modifier le contenu : editer cahier.txt (mode d'emploi : NOTATION.md),
pas ce script.

Prerequis : MuseScore 4 (https://musescore.org) et qpdf (`brew install qpdf`).
Chemins surchargeables via les variables d'env MSCORE et QPDF.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

# ---------------------------------------------------------------------------
# 1) CONTENU : lu dans cahier.txt (format documente dans NOTATION.md)
# ---------------------------------------------------------------------------
#
# Le contenu musical et pedagogique n'est PAS dans ce script : il est dans
# CONTENT_FILE, un fichier texte editable par un non-technicien.
# load_cahier() le transforme en :
#   [ {title, pages: [ {title, instruction, time, exercises:
#        [ {time, lines: [texte, ...], src: [no de ligne, ...]} ] } ] } ]

CONTENT_FILE = Path("cahier.txt")
DEFAULT_TIME = "4/4"


def load_cahier(path=CONTENT_FILE):
    chapters = []
    page = exercise = None

    def fail(lineno, msg):
        sys.exit(f"{path}, ligne {lineno} : {msg}")

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.rstrip()
        text = line.strip()
        if not text or text.startswith("//"):
            continue
        if text.startswith("## "):
            if not chapters:
                fail(lineno, "une leçon (##) doit être dans un chapitre (# Chapitre ...)")
            page = {"title": text[3:].strip(), "instruction": "", "time": DEFAULT_TIME,
                    "exercises": [], "src": lineno}
            chapters[-1]["pages"].append(page)
            exercise = None
        elif text.startswith("# "):
            title = text[2:].strip()
            # « Chapitre 3 : titre » -> « titre » (le numero est automatique)
            head, sep, rest = title.partition(":")
            if sep and head.strip().lower().startswith("chapitre"):
                title = rest.strip()
            chapters.append({"title": title, "pages": []})
            page = exercise = None
        elif page is None:
            fail(lineno, f"texte hors d'une leçon : « {text} » (ajouter une ligne « ## titre » avant)")
        elif text.lower().startswith("consigne"):
            page["instruction"] = text.partition(":")[2].strip()
        elif text.lower().startswith("mesure"):
            page["time"] = text.partition(":")[2].strip()
        elif text.startswith("- "):
            body, time_sig = text[2:].strip(), page["time"]
            head, sep, rest = body.partition(":")
            if sep and "/" in head:  # « - 3/4 : b n | ... »
                time_sig, body = head.strip(), rest.strip()
            exercise = {"time": time_sig, "lines": [body], "src": [lineno]}
            page["exercises"].append(exercise)
        elif line.startswith(" ") and exercise is not None:
            exercise["lines"].append(text)
            exercise["src"].append(lineno)
        else:
            fail(lineno, f"ligne non comprise : « {text} » "
                         "(un exercice commence par « - », sa 2e ligne par 2 espaces)")

    for chapter in chapters:
        for page in chapter["pages"]:
            if not page["exercises"]:
                fail(page["src"], f"la leçon « {page['title']} » n'a aucun exercice")
    if not chapters:
        sys.exit(f"{path} : aucun chapitre trouvé")
    return chapters


# ---------------------------------------------------------------------------
# 2) REGLAGES DE MISE EN PAGE
# ---------------------------------------------------------------------------

OUTPUT_PDF = "cahier_rythme.pdf"
BUILD_DIR = Path("build")

# Taille de la gravure : hauteur (mm) d'un "espace de portee" x4.
# Plus grand = notes plus grosses. 7 mm ~ standard, 9 mm ~ confortable enfant.
STAFF_SIZE_MM = 8.5
# Ecart vertical entre deux lignes (en dixiemes, 40 = hauteur d'une portee).
SYSTEM_DISTANCE = 140
PAGE_W_MM, PAGE_H_MM = 210, 297
MARGIN_MM = 15

# Style MuseScore applique a toutes les pages (cles = reglages MuseScore 4).
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
</Style></museScore>
"""

# ---------------------------------------------------------------------------
# 3) VALEURS RYTHMIQUES (1 temps = 12 divisions : divisible par 3 et par 4)
# ---------------------------------------------------------------------------

DIVISIONS = 12  # divisions MusicXML par noire
BEAT = DIVISIONS

TOKENS = {
    # token: (duree en divisions, type MusicXML, est_un_silence, pointe)
    "r": (48, "whole", False, False),
    "b.": (36, "half", False, True),
    "b": (24, "half", False, False),
    "n.": (18, "quarter", False, True),
    "n": (12, "quarter", False, False),
    "c.": (9, "eighth", False, True),
    "c": (6, "eighth", False, False),
    "t": (4, "eighth", False, False),   # croche de triolet (3 dans 1 temps)
    "d": (3, "16th", False, False),
    "p": (None, "whole", True, False),  # duree = mesure entiere
    "dp": (24, "half", True, False),
    "s": (12, "quarter", True, False),
    "ds": (6, "eighth", True, False),
}
BEAM_LEVELS = {"eighth": 1, "16th": 2}


def duration(token, measure_len):
    dur = TOKENS[token][0]
    return measure_len if dur is None else dur


def parse_time(time_sig, where):
    try:
        beats, beat_type = (int(x) for x in time_sig.split("/"))
    except ValueError:
        sys.exit(f"{where} : chiffrage invalide « {time_sig} »")
    if beat_type != 4:
        sys.exit(f"{where} : seuls les chiffrages en /4 sont gérés ({time_sig})")
    return beats


def parse_line(line, beats, where):
    """Decoupe une ligne en mesures et verifie symboles, durees et triolets."""
    measure_len = beats * BEAT
    measures = []
    for m_idx, chunk in enumerate(line.split("|"), start=1):
        here = f"{where}, mesure {m_idx} ({chunk.strip()})"
        tokens = chunk.split()
        for t in tokens:
            if t not in TOKENS:
                sys.exit(f"{here} : symbole inconnu « {t} »")
        if "p" in tokens and tokens != ["p"]:
            sys.exit(f"{here} : la pause « p » doit être seule dans sa mesure")
        # Triolets : groupes de 3 « t » commencant sur un temps
        pos, i = 0, 0
        while i < len(tokens):
            if tokens[i] == "t":
                if pos % BEAT or tokens[i:i + 3] != ["t"] * 3:
                    sys.exit(f"{here} : un triolet = 3 « t » au début d'un temps")
                pos, i = pos + BEAT, i + 3
            else:
                pos, i = pos + duration(tokens[i], measure_len), i + 1
        if pos != measure_len:
            sys.exit(f"{here} : {pos / BEAT:g} temps au lieu de {beats}")
        measures.append(tokens)
    return measures


# ---------------------------------------------------------------------------
# 4) LIGATURES : regroupe les croches/doubles/triolets d'un meme temps
# ---------------------------------------------------------------------------

def compute_beams(tokens):
    """Retourne, pour chaque note de la mesure, un dict {niveau: valeur}
    de ligatures MusicXML (begin/continue/end/forward hook/backward hook)."""
    beams = [dict() for _ in tokens]
    groups, current, pos = [], [], 0
    for i, t in enumerate(tokens):
        dur, kind, is_rest, _ = TOKENS[t]
        beamable = kind in BEAM_LEVELS and not is_rest
        if beamable and current and pos // BEAT == current_beat:
            current.append(i)
        else:
            if len(current) > 1:
                groups.append(current)
            current = [i] if beamable else []
            current_beat = pos // BEAT
        pos += dur or 0
    if len(current) > 1:
        groups.append(current)

    for g in groups:
        for k, i in enumerate(g):
            beams[i][1] = "begin" if k == 0 else "end" if k == len(g) - 1 else "continue"
        # 2e barre : sur les suites de doubles-croches consecutives
        k = 0
        while k < len(g):
            if TOKENS[tokens[g[k]]][1] != "16th":
                k += 1
                continue
            run = [g[k]]
            while k + 1 < len(g) and TOKENS[tokens[g[k + 1]]][1] == "16th":
                k += 1
                run.append(g[k])
            if len(run) == 1:
                beams[run[0]][2] = "backward hook" if run[0] == g[-1] else "forward hook"
            else:
                for j, i in enumerate(run):
                    beams[i][2] = "begin" if j == 0 else "end" if j == len(run) - 1 else "continue"
            k += 1
    return beams


# ---------------------------------------------------------------------------
# 5) GENERATION MUSICXML
# ---------------------------------------------------------------------------

def note_xml(token, beams, measure_len, pos):
    _, kind, is_rest, dotted = TOKENS[token]
    out = ["<note>"]
    if is_rest:
        out.append('<rest measure="yes"/>' if token == "p" else "<rest/>")
    else:
        out.append("<unpitched><display-step>B</display-step>"
                   "<display-octave>4</display-octave></unpitched>")
    out.append(f"<duration>{duration(token, measure_len)}</duration>")
    if not is_rest:
        out.append('<instrument id="P1-I1"/>')
    out.append(f"<voice>1</voice><type>{kind}</type>")
    if dotted:
        out.append("<dot/>")
    if token == "t":
        out.append("<time-modification><actual-notes>3</actual-notes>"
                   "<normal-notes>2</normal-notes></time-modification>")
    if not is_rest and kind != "whole":
        out.append("<stem>up</stem>")
    for level in sorted(beams):
        out.append(f'<beam number="{level}">{beams[level]}</beam>')
    if token == "t" and pos % BEAT in (0, 2 * BEAT // 3):
        kind_tuplet = "start" if pos % BEAT == 0 else "stop"
        out.append(f'<notations><tuplet type="{kind_tuplet}" number="1" bracket="no"/></notations>')
    out.append("</note>")
    return "".join(out)


def page_to_musicxml(chapter_no, chapter, page_no, page):
    tenths_per_mm = 40 / STAFF_SIZE_MM
    pw, ph = PAGE_W_MM * tenths_per_mm, PAGE_H_MM * tenths_per_mm
    mg = MARGIN_MM * tenths_per_mm
    lesson = f"{chapter_no}.{page_no}"

    measures_xml, number = [], 0
    for ex_no, exercise in enumerate(page["exercises"], start=1):
        lines, src = exercise["lines"], exercise["src"]
        where = f"{CONTENT_FILE}, ligne {src[0]} (exercice {lesson}.{ex_no})"
        beats = parse_time(exercise["time"], where)
        if len(lines) > 2:
            sys.exit(f"{where} : un exercice fait 1 ou 2 lignes, pas {len(lines)}")
        parsed = [parse_line(l, beats, f"{CONTENT_FILE}, ligne {n} (exercice {lesson}.{ex_no})")
                  for l, n in zip(lines, src)]

        for line_idx, measures in enumerate(parsed):
            for m_idx, tokens in enumerate(measures):
                number += 1
                parts = [f'<measure number="{number}">']
                if m_idx == 0 and number > 1:
                    parts.append('<print new-system="yes"/>')
                if line_idx == 0 and m_idx == 0:
                    # Debut d'exercice : chiffrage (re)affiche + repere encadre N.M.K
                    attrs = ""
                    if number == 1:
                        attrs += (f"<divisions>{DIVISIONS}</divisions>"
                                  '<key print-object="no"><fifths>0</fifths></key>')
                    attrs += f"<time><beats>{beats}</beats><beat-type>4</beat-type></time>"
                    if number == 1:
                        attrs += ("<staff-details><staff-lines>1</staff-lines></staff-details>"
                                  "<clef><sign>percussion</sign></clef>")
                    parts.append(f"<attributes>{attrs}</attributes>")
                    parts.append('<direction placement="above"><direction-type>'
                                 f'<rehearsal enclosure="rectangle">{lesson}.{ex_no}</rehearsal>'
                                 "</direction-type></direction>")
                beams = compute_beams(tokens)
                pos = 0
                for t, b in zip(tokens, beams):
                    parts.append(note_xml(t, b, beats * BEAT, pos))
                    pos += duration(t, beats * BEAT)
                if line_idx == len(parsed) - 1 and m_idx == len(measures) - 1:
                    parts.append('<barline location="right"><bar-style>light-heavy</bar-style></barline>')
                parts.append("</measure>")
                measures_xml.append("".join(parts))

    chap = escape(f"Chapitre {chapter_no} · {chapter['title']}")
    title = escape(f"{lesson}  {page['title']}")
    instr = escape(page["instruction"])
    # En-tete = un seul texte sur 3 lignes (chapitre / titre / consigne) :
    # MuseScore empile mal plusieurs credits distincts (chevauchements).
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="4.0">
  <work><work-title>{title}</work-title></work>
  <defaults>
    <scaling><millimeters>{STAFF_SIZE_MM}</millimeters><tenths>40</tenths></scaling>
    <page-layout>
      <page-height>{ph:.0f}</page-height><page-width>{pw:.0f}</page-width>
      <page-margins type="both"><left-margin>{mg:.0f}</left-margin><right-margin>{mg:.0f}</right-margin>
      <top-margin>{mg:.0f}</top-margin><bottom-margin>{mg:.0f}</bottom-margin></page-margins>
    </page-layout>
    <system-layout><system-distance>{SYSTEM_DISTANCE}</system-distance><top-system-distance>150</top-system-distance></system-layout>
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


# ---------------------------------------------------------------------------
# 6) RENDU (MuseScore) ET FUSION (qpdf)
# ---------------------------------------------------------------------------

def find_tool(env_var, candidates):
    for c in [os.environ.get(env_var), *candidates]:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    sys.exit(f"Outil introuvable ({env_var}). Installez-le ou definissez la variable {env_var}.")


def build():
    mscore = find_tool("MSCORE", ["/Applications/MuseScore 4.app/Contents/MacOS/mscore", "mscore", "musescore"])
    qpdf = find_tool("QPDF", ["qpdf", "/opt/homebrew/bin/qpdf"])

    BUILD_DIR.mkdir(exist_ok=True)
    for old in [*BUILD_DIR.glob("page_*.musicxml"), *BUILD_DIR.glob("page_*.pdf")]:
        old.unlink()  # evite de garder des pages d'une version plus longue
    jobs, pdfs = [], []
    for c_no, chapter in enumerate(load_cahier(), start=1):
        for p_no, page in enumerate(chapter["pages"], start=1):
            stem = f"page_{len(pdfs) + 1:02d}"
            xml_path, pdf_path = BUILD_DIR / f"{stem}.musicxml", BUILD_DIR / f"{stem}.pdf"
            xml_path.write_text(page_to_musicxml(c_no, chapter, p_no, page), encoding="utf-8")
            jobs.append({"in": str(xml_path.resolve()), "out": str(pdf_path.resolve())})
            pdfs.append(str(pdf_path))

    style_file = BUILD_DIR / "style.mss"
    style_file.write_text(STYLE_MSS)
    job_file = BUILD_DIR / "job.json"
    job_file.write_text(json.dumps(jobs, indent=2))
    # MuseScore 4.7 peut avorter (SIGABRT, "mutex lock failed") dans exit(),
    # APRES avoir ecrit les PDF : bug de destruction des statiques cote
    # MuseScore. On juge donc le resultat sur les fichiers, pas le code retour.
    log_file = BUILD_DIR / "mscore.log"
    with log_file.open("w") as log:
        rc = subprocess.run([mscore, "-S", str(style_file.resolve()), "-j", str(job_file)],
                            stdout=log, stderr=subprocess.STDOUT).returncode
    missing = [p for p in pdfs if not Path(p).exists()]
    if missing:
        sys.exit(f"MuseScore n'a pas produit : {', '.join(missing)} (voir {log_file})")
    if rc != 0:
        print(f"Note : MuseScore a quitte avec le code {rc} apres export (bug connu a la fermeture, sans impact).")

    subprocess.run([qpdf, "--empty", "--pages", *pdfs, "--", OUTPUT_PDF], check=True)
    print(f"PDF genere : {OUTPUT_PDF} ({len(pdfs)} pages)")


if __name__ == "__main__":
    build()
