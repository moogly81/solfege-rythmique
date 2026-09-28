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

\layout {
  \context {
    \Score
    \remove "Bar_number_engraver"
    \override TimeSignature.break-visibility = #end-of-line-invisible
  }
}

rythme = {
  \autoBeamOff
  \numericTimeSignature
  \override Staff.StaffSymbol.line-count = #1
  \override Stem.direction = #UP
  \clef "percussion"
  \time 4/4 \mark \markup { \box "1.1.1" } c'1 | c'2. c'4 | c'2 r2 | c'4. c'8 r4 r8 c'8 \bar "|." | \break \mark \markup { \box "1.1.2" } c'8[ c'8] c'16[ c'16 c'16 c'16] \once \override TupletBracket.bracket-visibility = ##f \tuplet 3/2 { c'8[ c'8 c'8] } c'8.[ c'16] | R1 \bar "|." | \break \time 3/4 \mark \markup { \box "1.1.3" } c'2. | c'4 c'4 c'4 | c'8 c'4 c'8 c'4 | \break c'8[ c'16 c'16] c'16[ c'16 c'8] \once \override TupletBracket.bracket-visibility = ##f \tuplet 3/2 { c'8[ c'8 c'8] } | R2. \bar "|." | \break \time 2/4 \mark \markup { \box "1.1.4" } c'8[ c'8] c'16[ c'16 c'16 c'16] | c'4. c'8 | c'8.[ c'16] c'8[ c'16 c'16] | c'2 \bar "|." |
}

cachee = {
  c'1 c'2. c'4 c'2 c'2 c'4. c'8 c'4 c'8 c'8 c'8 c'8 c'16 c'16 c'16 c'16 \tuplet 3/2 { c'8 c'8 c'8 } c'8. c'16 c'1 c'2. c'4 c'4 c'4 c'8 c'4 c'8 c'4 c'8 c'16 c'16 c'16 c'16 c'8 \tuplet 3/2 { c'8 c'8 c'8 } c'2. c'8 c'8 c'16 c'16 c'16 c'16 c'4. c'8 c'8. c'16 c'8 c'16 c'16 c'2
}

paroles = \lyricmode {
  "ron-de lon-gue" blan-che noir blan-che chut noi-re croch' chut ch croch \skip 8 \skip 8 \skip 16 \skip 16 \skip 16 \skip 16 \skip 8 \skip 8 \skip 8 \skip 8. \skip 16 \skip 1 \skip 2. \skip 4 \skip 4 \skip 4 \skip 8 \skip 4 \skip 8 \skip 4 \skip 8 \skip 16 \skip 16 \skip 16 \skip 16 \skip 8 \skip 8 \skip 8 \skip 8 \skip 2. \skip 8 \skip 8 \skip 16 \skip 16 \skip 16 \skip 16 \skip 4. \skip 8 \skip 8. \skip 16 \skip 8 \skip 16 \skip 16 \skip 2
}

\bookpart {
  \paper {
    #(define (page-post-process layout pages) (ly:message "solfege-pages 1.1 ~a" (length pages)))
  }
  \markup \fill-line {
    \center-column {
      \abs-fontsize #12 "Chapitre 1 · Référence & <essai>"
      \abs-fontsize #22 \bold "1.1  Toutes les valeurs"
      \abs-fontsize #13 \italic "Ne pas modifier sans régénérer la référence."
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
  }
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

\bookpart {
  \paper {
    #(define (page-post-process layout pages) (ly:message "solfege-pages 1.2 ~a" (length pages)))
  }
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
  }
}
