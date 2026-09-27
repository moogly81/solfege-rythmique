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

\header {
  tagline = ##f
}

rythme = {
  \autoBeamOff
  \numericTimeSignature
  \override Staff.StaffSymbol.line-count = #1
  \override Stem.direction = #UP
  \clef "percussion"
  \time 4/4 \mark \markup { \box "1.2.1" } c'4 c'4 c'2 | c'1 \bar "|." |
}

cachee = {
  c'4 c'4 c'2 c'1
}

paroles = \lyricmode {
  \skip 4 \skip 4 \skip 2 \skip 1
}

\book {
  \markup \fill-line {
    \center-column {
      \abs-fontsize #12 "Chapitre 1 · Référence & <essai>"
      \abs-fontsize #22 \bold "1.2  Deuxième page"
      \abs-fontsize #13 \italic "Une 2e leçon pour tester la numérotation des pages."
    }
  }
  \score {
    <<
      \new Staff <<
        \new Voice = "rythme" \rythme
        \new NullVoice = "cachee" \cachee
      >>
      \new Lyrics \lyricsto "cachee" \paroles
    >>
    \layout {
      \context { \Score \remove "Bar_number_engraver" }
    }
  }
}
