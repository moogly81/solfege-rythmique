"""Étape 1 : lecture de cahier.txt (format documenté dans NOTATION.md).

Ne vérifie que la structure (chapitres, leçons, exercices) ; les rythmes
sont vérifiés par solfege.rythme.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path

from .config import DEFAULT_TIME
from .erreurs import CahierError

MAX_LINES_PER_EXERCISE = 2


@dataclass(frozen=True)
class SourceLine:
    text: str
    where: str  # « cahier.txt, ligne 12 »
    syllables: str | None = None  # ligne « = ... » : syllabes à afficher sous les notes
    syllables_where: str = ""


@dataclass
class Exercise:
    number: str  # « 2.1.3 »
    time: str
    lines: list[SourceLine]

    @property
    def where(self) -> str:
        return f"{self.lines[0].where} (exercice {self.number})"


@dataclass
class Lesson:
    number: str  # « 2.1 »
    title: str
    where: str
    instruction: str = ""
    time: str = DEFAULT_TIME
    exercises: list[Exercise] = field(default_factory=list)


@dataclass
class Chapter:
    number: int
    title: str
    lessons: list[Lesson] = field(default_factory=list)


@dataclass
class Cahier:
    source: str
    chapters: list[Chapter]

    def lessons(self) -> Iterator[tuple[Chapter, Lesson]]:
        for chapter in self.chapters:
            for lesson in chapter.lessons:
                yield chapter, lesson


def load_cahier(path: Path) -> Cahier:
    # utf-8-sig : accepte le BOM que certains éditeurs (Bloc-notes) ajoutent en tête de fichier
    return parse_cahier(path.read_text(encoding="utf-8-sig"), source=str(path))


def _field_value(stripped: str, name: str, where: str) -> str:
    """« Consigne : texte » -> « texte » ; refuse l'absence de « : »."""
    head, sep, value = stripped.partition(":")
    if not sep:
        raise CahierError(f"{where} : « {head.strip()} » doit être suivi de « : » (exemple : « {name} : ... »)")
    return value.strip()


def _chapter_title(text: str) -> str:
    # « Chapitre 3 : titre » -> « titre » (le numéro est automatique)
    head, sep, rest = text.partition(":")
    if sep and head.strip().lower().startswith("chapitre"):
        return rest.strip()
    return text


def parse_cahier(text: str, source: str = "cahier.txt") -> Cahier:
    chapters: list[Chapter] = []
    lesson: Lesson | None = None
    exercise: Exercise | None = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        where = f"{source}, ligne {lineno}"

        def fail(msg: str, where: str = where) -> CahierError:
            return CahierError(f"{where} : {msg}")

        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        indented = raw[:1] in (" ", "\t", " ")  # 2e ligne d'exercice ou syllabes : décalée
        if stripped.startswith("## "):
            if not chapters:
                raise fail("une leçon (##) doit être dans un chapitre (# Chapitre ...)")
            chapter = chapters[-1]
            lesson = Lesson(f"{chapter.number}.{len(chapter.lessons) + 1}", stripped[3:].strip(), where)
            chapter.lessons.append(lesson)
            exercise = None
        elif stripped.startswith("# "):
            chapters.append(Chapter(len(chapters) + 1, _chapter_title(stripped[2:].strip())))
            lesson = exercise = None
        elif lesson is None:
            raise fail(f"texte hors d'une leçon : « {stripped} » (ajouter une ligne « ## titre » avant)")
        elif stripped.lower().startswith("consigne"):
            lesson.instruction = _field_value(stripped, "Consigne", where)
        elif stripped.lower().startswith("mesure"):
            if lesson.exercises:
                raise fail("« Mesure : » doit être placée avant le 1er exercice de la leçon")
            lesson.time = _field_value(stripped, "Mesure", where)
        elif stripped.startswith("- "):
            body, time_sig = stripped[2:].strip(), lesson.time
            head, sep, rest = body.partition(":")
            if sep and "/" in head:  # « - 3/4 : b n | ... »
                time_sig, body = head.strip(), rest.strip()
            number = f"{lesson.number}.{len(lesson.exercises) + 1}"
            exercise = Exercise(number, time_sig, [SourceLine(body, where)])
            lesson.exercises.append(exercise)
        elif stripped.startswith("=") and indented and exercise is not None:
            last = exercise.lines[-1]
            if last.syllables is not None:
                raise fail("une seule ligne de syllabes « = » sous chaque ligne de rythme")
            exercise.lines[-1] = replace(last, syllables=stripped[1:].strip(), syllables_where=where)
        elif indented and exercise is not None:
            exercise.lines.append(SourceLine(stripped, where))
        else:
            raise fail(
                f"ligne non comprise : « {stripped} » "
                "(un exercice commence par « - », sa 2e ligne par 2 espaces ou une tabulation)"
            )

    if not chapters:
        raise CahierError(f"{source} : aucun chapitre trouvé")
    for _, lesson in Cahier(source, chapters).lessons():
        if not lesson.exercises:
            raise CahierError(f"{lesson.where} : la leçon « {lesson.title} » n'a aucun exercice")
        for ex in lesson.exercises:
            if len(ex.lines) > MAX_LINES_PER_EXERCISE:
                raise CahierError(f"{ex.where} : un exercice fait 1 ou 2 lignes, pas {len(ex.lines)}")
    return Cahier(source, chapters)
