#!/usr/bin/env python3
"""
Cahier de lecture rythmique (4/4, ligne rythmique unique).

Pipeline : contenu (PAGES) -> un fichier MusicXML par page -> PDF via
MuseScore 4 (gravure pro, police Leland) -> fusion des pages avec qpdf.

Pour modifier le contenu : voir la section "CONTENU DES PAGES" plus bas.

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
# 1) CONTENU DES PAGES
# ---------------------------------------------------------------------------
#
# Chaque page : un titre, une consigne, et une liste de lignes.
# Chaque ligne est une chaine : les mesures sont separees par "|",
# les notes par des espaces. Chaque mesure doit faire 4 temps (verifie).
#
#   r  = ronde (4)        p  = pause (4)
#   b  = blanche (2)      dp = demi-pause (2)
#   n  = noire (1)        s  = soupir (1)
#   c  = croche (1/2)     ds = demi-soupir (1/2)
#   d  = double-croche (1/4)
#
# Les croches / doubles-croches d'un meme temps sont automatiquement reliees
# (ligatures), sauf si un silence les separe.

PAGES = [
    {
        "title": "1. La ronde et la pause",
        "instruction": "Ronde = 4 temps (frappe sur 1). Pause = 4 temps de silence.",
        "lines": [
            "r | r | r | r",
            "r | p | r | p",
            "p | r | p | r",
            "r | r | p | r",
            "r | p | p | r",
            "p | r | r | p",
            "r | p | r | r",
            "p | p | r | r",
        ],
    },
    {
        "title": "2. La blanche",
        "instruction": "La blanche dure 2 temps : frappe sur 1 et sur 3.",
        "lines": [
            "b b | b b | b b | b b",
            "r | b b | r | b b",
            "b b | r | b b | p",
            "r | p | b b | b b",
            "b b | b b | r | p",
            "p | b b | r | b b",
            "b b | r | p | r",
            "r | b b | p | b b",
        ],
    },
    {
        "title": "3. La demi-pause",
        "instruction": "La demi-pause = 2 temps de silence. Elle est posée sur la ligne (la pause est accrochée dessous).",
        "lines": [
            "b dp | b dp | dp b | dp b",
            "b b | b dp | b b | dp b",
            "r | b dp | r | dp b",
            "dp b | b b | b dp | r",
            "b dp | p | dp b | r",
            "b b | dp b | p | b dp",
            "r | dp b | b dp | p",
            "dp b | b b | r | b dp",
        ],
    },
    {
        "title": "4. Révision : rondes, blanches, pauses et demi-pauses",
        "instruction": "Frappe les notes, compte les silences dans ta tête.",
        "lines": [
            "r | b b | p | b dp",
            "b dp | r | dp b | p",
            "b b | p | r | b b",
            "dp b | b dp | b b | r",
            "r | dp b | p | b b",
            "p | b b | b dp | r",
            "b dp | dp b | r | p",
            "b b | r | dp b | r",
        ],
    },
    {
        "title": "5. La noire",
        "instruction": "Compte 1 - 2 - 3 - 4 : la noire dure 1 temps.",
        "lines": [
            "n n n n | n n n n | n n n n | n n n n",
            "n n b | b n n | r | n n n n",
            "b b | n n b | p | n n n n",
            "n b n | n n b | b dp | r",
            "r | n n n n | b n n | dp b",
            "n n n n | n b n | p | b b",
            "b n n | r | n n b | n n n n",
            "dp n n | n b n | b n n | r",
        ],
    },
    {
        "title": "6. Le soupir",
        "instruction": "Le soupir = 1 temps de silence.",
        "lines": [
            "n n n s | n n n s | n s n s | r",
            "s n n n | b n s | n n s n | b dp",
            "n s n s | s n b | n n s s | p",
            "b n s | s n n n | dp n s | r",
            "s n s n | n n b | n s s n | b b",
            "n s n n | b s n | s n n s | r",
            "n n n n | n s n s | s n b | dp b",
            "n s b | n n s n | b n s | p",
        ],
    },
    {
        "title": "7. Révision : noires, blanches, rondes et silences",
        "instruction": "Regarde bien chaque signe : note ou silence ? Combien de temps ?",
        "lines": [
            "n n b | b s n | n n n s | r",
            "b dp | n s n n | r | n n b",
            "n s b | p | n n n n | b dp",
            "r | n n s n | dp n n | b b",
            "n n n s | b n s | dp b | r",
            "b n n | s n b | p | n n n n",
            "n s n s | r | b dp | n n b",
            "dp n n | n n b | n s n s | r",
        ],
    },
    {
        "title": "8. La croche",
        "instruction": "Compte 1 et 2 et 3 et 4 et : deux croches = 1 temps.",
        "lines": [
            "c c c c c c c c | n n n n | c c c c c c c c | r",
            "c c n n n | n c c n n | b c c n | r",
            "n n c c n | c c n b | n n n c c | b b",
            "c c c c b | n c c n n | r | n n c c n",
            "b c c c c | c c n n n | n n b | c c c c b",
            "n c c n n | b n c c | c c c c n n | r",
            "c c n c c n | r | n n c c n | b b",
            "b n c c | c c c c n n | n c c b | r",
        ],
    },
    {
        "title": "9. Croches avec tout ce que tu connais",
        "instruction": "Croches, noires, blanches, rondes... et les silences !",
        "lines": [
            "c c s n n | b c c s | c c c c dp | r",
            "dp c c n | s c c b | n n c c s | p",
            "c c n b | c c c c s n | dp n c c | r",
            "s c c c c n | b s n | c c n c c n | p",
            "n c c s c c | dp c c s | b c c n | r",
            "c c c c c c n | s n b | c c s c c s | p",
            "b c c s | n n c c n | dp s c c | r",
            "c c n s n | c c c c b | s c c b | p",
        ],
    },
    {
        "title": "10. Le demi-soupir",
        "instruction": "Le demi-soupir = 1/2 temps de silence (la moitié d'un soupir).",
        "lines": [
            "n n s n | n s n s | c c s c c n | n n n s",
            "c c n s n | s n c c n | n s c c s | c c c c n s",
            "n c ds n n | c ds c ds n n | n n c ds n | c c c ds n s",
            "ds c n n n | n ds c n n | ds c ds c n n | n n ds c n",
            "c c s c ds n | n ds c s n | c c c c s n | n s n s",
            "s n c c n | ds c c c s n | n n ds c s | c c n n s",
            "c ds c ds n n | n n s c c | ds c c c n s | n s c c n",
            "n n c c s | c c ds c n s | s c c ds c n | n n n s",
        ],
    },
    {
        "title": "11. Croches et tous les silences",
        "instruction": "Pause 4 temps, demi-pause 2 temps, soupir 1 temps, demi-soupir 1/2 temps.",
        "lines": [
            "c c n s n | b dp | c ds c c n n | p",
            "ds c c c b | n s dp | c c c c n s | r",
            "b c c n | dp c c n | n ds c s n | p",
            "c c s b | ds c n dp | p | c c c c b",
            "n n c c s | b ds c n | dp c c c c | r",
            "c ds c ds b | p | n s c c n | dp b",
            "dp n c c | c c n b | s n ds c n | p",
            "b s n | c c c c dp | ds c n b | r",
        ],
    },
    {
        "title": "12. La double-croche",
        "instruction": "Compte 1-i-et-a : quatre doubles-croches = 1 temps.",
        "lines": [
            "d d d d n n n | n d d d d n n | n n d d d d n",
            "n n n d d d d | d d d d d d d d n n | n n n n",
            "d d d d n d d d d n | n d d d d n d d d d | d d d d d d d d d d d d n",
            "n n d d d d d d d d | d d d d n n n | n d d d d n n",
            "d d d d d d d d d d d d d d d d | n n n n | d d d d n d d d d n",
            "n d d d d d d d d n | d d d d n n n | n n n n",
            "d d d d n n d d d d | n n d d d d n | d d d d d d d d n n",
            "n n n d d d d | d d d d n d d d d n | n n n n",
        ],
    },
    {
        "title": "13. Doubles-croches et croches",
        "instruction": "Croches « 1 et », doubles « 1-i-et-a » : écoute la différence !",
        "lines": [
            "d d d d n n n | n d d d d n n | n n n d d d d",
            "d d d d d d d d n n | n n d d d d d d d d | n n n n",
            "d d d d c c n n | c c d d d d n n | n d d d d c c n",
            "d d d d n d d d d n | c c c c n n | n n c c d d d d",
            "c c d d d d c c n | n d d d d n n | n n n n",
            "n n d d d d n | d d d d c c n n | d d d d n n n",
            "d d d d n c c n | c c c c d d d d n | n n n n",
            "n c c d d d d n | d d d d d d d d n n | c c d d d d c c n",
        ],
    },
    {
        "title": "14. Doubles-croches et silences",
        "instruction": "Garde bien le temps pendant les silences.",
        "lines": [
            "d d d d s c c n | c c d d d d s n | d d d d c ds n s",
            "n s d d d d c c | ds c d d d d n s | b d d d d s",
            "d d d d d d d d dp | s d d d d c c n | p",
            "c c d d d d s n | dp d d d d c c | n ds c d d d d s",
            "d d d d n s n | c ds c ds d d d d n | b dp",
            "s d d d d s d d d d | n n c c s | d d d d c c b",
            "dp d d d d n | c c s d d d d n | r",
            "d d d d c c n s | ds c c ds d d d d n | p",
        ],
    },
    {
        "title": "15. Révision générale (1)",
        "instruction": "Toutes les valeurs : prends ton temps, compte bien.",
        "lines": [
            "r | b dp | n s b | c c c c b",
            "d d d d n n n | p | b c c n | dp b",
            "n n s n | d d d d c c b | r | b b",
            "c c ds c b | n d d d d s n | dp n n | r",
            "p | d d d d n c c n | b s n | r",
            "b b | c c s d d d d n | n ds c b | p",
            "d d d d d d d d b | r | n s c c n | b dp",
            "n c c d d d d n | s n b | dp c c n | r",
        ],
    },
    {
        "title": "16. Révision générale (2)",
        "instruction": "Toutes les notes et tous les silences : bravo, tu sais tout lire !",
        "lines": [
            "r | b b | n n b | n n n n",
            "c c n n n | b c c n | d d d d n n n | r",
            "n s n s | c c ds c n n | b s n | p",
            "d d d d c c n n | n n c c d d d d | b b | r",
            "n ds c b | c c c c n n | dp n n | r",
            "d d d d d d d d n n | c c n s n | n n c c ds c | b b",
            "b n n | c c d d d d n s | ds c n n n | r",
            "n c c n c c | d d d d n b | s n c c n | p",
        ],
    },
]


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
</Style></museScore>
"""

# ---------------------------------------------------------------------------
# 3) VALEURS RYTHMIQUES (en doubles-croches : 1 temps = 4)
# ---------------------------------------------------------------------------

DIVISIONS = 4  # divisions MusicXML par noire
BEAT = DIVISIONS

TOKENS = {
    # token: (duree en divisions, type MusicXML, est_un_silence)
    "r": (16, "whole", False),
    "b": (8, "half", False),
    "n": (4, "quarter", False),
    "c": (2, "eighth", False),
    "d": (1, "16th", False),
    "p": (16, "whole", True),
    "dp": (8, "half", True),
    "s": (4, "quarter", True),
    "ds": (2, "eighth", True),
}
BEAM_LEVELS = {"eighth": 1, "16th": 2}


def parse_line(line, where):
    measures = []
    for m_idx, chunk in enumerate(line.split("|"), start=1):
        tokens = chunk.split()
        for t in tokens:
            if t not in TOKENS:
                sys.exit(f"{where}, mesure {m_idx} : symbole inconnu « {t} »")
        total = sum(TOKENS[t][0] for t in tokens)
        if total != 4 * BEAT:
            sys.exit(f"{where}, mesure {m_idx} : {total / BEAT:g} temps au lieu de 4 ({chunk.strip()})")
        measures.append(tokens)
    return measures


# ---------------------------------------------------------------------------
# 4) LIGATURES : regroupe les croches/doubles d'un meme temps
# ---------------------------------------------------------------------------

def compute_beams(tokens):
    """Retourne, pour chaque note de la mesure, un dict {niveau: valeur}
    de ligatures MusicXML (begin/continue/end/forward hook/backward hook)."""
    beams = [dict() for _ in tokens]
    groups, current, pos = [], [], 0
    for i, t in enumerate(tokens):
        dur, kind, is_rest = TOKENS[t]
        beamable = kind in BEAM_LEVELS and not is_rest
        if beamable and current and pos // BEAT == current_beat:
            current.append(i)
        else:
            if len(current) > 1:
                groups.append(current)
            current = [i] if beamable else []
            current_beat = pos // BEAT
        pos += dur
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

def note_xml(token, beams, whole_measure):
    dur, kind, is_rest = TOKENS[token]
    out = ["<note>"]
    if is_rest:
        out.append('<rest measure="yes"/>' if whole_measure else "<rest/>")
    else:
        out.append("<unpitched><display-step>B</display-step>"
                   "<display-octave>4</display-octave></unpitched>")
    out.append(f"<duration>{dur}</duration>")
    if not is_rest:
        out.append('<instrument id="P1-I1"/>')
    out.append(f"<voice>1</voice><type>{kind}</type>")
    if not is_rest and kind != "whole":
        out.append("<stem>up</stem>")
    for level in sorted(beams):
        out.append(f'<beam number="{level}">{beams[level]}</beam>')
    out.append("</note>")
    return "".join(out)


def page_to_musicxml(page, page_no):
    tenths_per_mm = 40 / STAFF_SIZE_MM
    pw, ph = PAGE_W_MM * tenths_per_mm, PAGE_H_MM * tenths_per_mm
    mg = MARGIN_MM * tenths_per_mm

    lines = [parse_line(l, f"Page {page_no}, ligne {i}") for i, l in enumerate(page["lines"], 1)]

    measures_xml, number = [], 0
    for line_idx, measures in enumerate(lines):
        for m_idx, tokens in enumerate(measures):
            number += 1
            parts = [f'<measure number="{number}">']
            if m_idx == 0:
                new_sys = ' new-system="yes"' if line_idx > 0 else ""
                parts.append(f"<print{new_sys}><measure-numbering>none</measure-numbering></print>")
            if number == 1:
                parts.append(
                    f"<attributes><divisions>{DIVISIONS}</divisions>"
                    "<key print-object=\"no\"><fifths>0</fifths></key>"
                    "<time><beats>4</beats><beat-type>4</beat-type></time>"
                    "<staff-details><staff-lines>1</staff-lines></staff-details>"
                    "<clef><sign>percussion</sign></clef></attributes>"
                )
            beams = compute_beams(tokens)
            whole = len(tokens) == 1
            parts += [note_xml(t, b, whole) for t, b in zip(tokens, beams)]
            if line_idx == len(lines) - 1 and m_idx == len(measures) - 1:
                parts.append('<barline location="right"><bar-style>light-heavy</bar-style></barline>')
            parts.append("</measure>")
            measures_xml.append("".join(parts))

    title, instr = escape(page["title"]), escape(page["instruction"])
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
    <system-layout><system-distance>{SYSTEM_DISTANCE}</system-distance><top-system-distance>120</top-system-distance></system-layout>
  </defaults>
  <credit page="1"><credit-type>title</credit-type>
    <credit-words justify="center" halign="center" valign="top" default-x="{pw / 2:.0f}" default-y="{ph - mg:.0f}" font-size="22" font-weight="bold">{title}</credit-words></credit>
  <credit page="1"><credit-type>subtitle</credit-type>
    <credit-words justify="center" halign="center" valign="top" default-x="{pw / 2:.0f}" default-y="{ph - mg - 40:.0f}" font-size="13" font-style="italic">{instr}</credit-words></credit>
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
    jobs, pdfs = [], []
    for i, page in enumerate(PAGES, start=1):
        xml_path = BUILD_DIR / f"page_{i:02d}.musicxml"
        pdf_path = BUILD_DIR / f"page_{i:02d}.pdf"
        xml_path.write_text(page_to_musicxml(page, i), encoding="utf-8")
        jobs.append({"in": str(xml_path.resolve()), "out": str(pdf_path.resolve())})
        pdfs.append(str(pdf_path))

    for p in pdfs:
        Path(p).unlink(missing_ok=True)
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
    print(f"PDF genere : {OUTPUT_PDF} ({len(PAGES)} pages)")


if __name__ == "__main__":
    build()
