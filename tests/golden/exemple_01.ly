\version "2.24.0"
#(set-global-staff-size 24.09)

\paper {
  #(set-paper-size "a4")
  top-margin = 15\mm
  bottom-margin = 15\mm
  left-margin = 15\mm
  right-margin = 15\mm
  indent = 0
  ragged-last-bottom = ##f
  print-page-number = ##f
  system-system-spacing.basic-distance = 14.0
  markup-system-spacing.basic-distance = 15.0
}

rythme = {
  \autoBeamOff
  \override Staff.StaffSymbol.line-count = #1
  \override Stem.direction = #UP
  \clef "percussion"
  \time 4/4 \mark \markup { \box "1.1.1" } c1 | c2. c4 | c2 r2 | c4. c8 r4 r8 c8 \bar "|." | \break \mark \markup { \box "1.1.2" } c8[ c8] c16[ c16 c16 c16] \once \override TupletBracket.bracket-visibility = ##f \tuplet 3/2 { c8[ c8 c8] } c8.[ c16] | R1 \bar "|." | \break \time 3/4 \mark \markup { \box "1.1.3" } c2. | c4 c4 c4 | c8 c4 c8 c4 | \break c8[ c16 c16] c16[ c16 c8] \once \override TupletBracket.bracket-visibility = ##f \tuplet 3/2 { c8[ c8 c8] } | R2. \bar "|." | \break \time 2/4 \mark \markup { \box "1.1.4" } c8[ c8] c16[ c16 c16 c16] | c4. c8 | c8.[ c16] c8[ c16 c16] | c2 \bar "|." |
}

paroles = \lyricmode {
  "ron-de lon-gue" blan-che noir blan-che chut noi-re croch' chut ch croch \skip 8 \skip 8 \skip 16 \skip 16 \skip 16 \skip 16 \skip 8 \skip 8 \skip 8 \skip 8. \skip 16 \skip 1 \skip 2. \skip 4 \skip 4 \skip 4 \skip 8 \skip 4 \skip 8 \skip 4 \skip 8 \skip 16 \skip 16 \skip 16 \skip 16 \skip 8 \skip 8 \skip 8 \skip 8 \skip 2. \skip 8 \skip 8 \skip 16 \skip 16 \skip 16 \skip 16 \skip 4. \skip 8 \skip 8. \skip 16 \skip 8 \skip 16 \skip 16 \skip 2
}

\book {
  \markup \fill-line {
    \center-column {
      \abs-fontsize #12 "Chapitre 1 · Référence & <essai>"
      \abs-fontsize #22 \bold "1.1  Toutes les valeurs"
      \abs-fontsize #13 \italic "Ne pas modifier sans régénérer la référence."
    }
  }
  \score {
    <<
      \new Staff \new Voice = "rythme" \rythme
      \addlyrics \paroles
    >>
    \layout {}
  }
}
