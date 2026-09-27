"""Étape 1 : lecture de cahier.txt (format documenté dans NOTATION.md).

Ne vérifie que la structure (chapitres, leçons, exercices) ; les rythmes
sont vérifiés par solfege.rythme.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from .config import DEFAULT_TIME
from .erreurs import CahierError

MAX_LINES_PER_EXERCISE = 2


@dataclass(frozen=True)
class SourceLine:
    text: str
    where: str  # « cahier.txt, ligne 12 »


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
    return parse_cahier(path.read_text(encoding="utf-8"), source=str(path))


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
            lesson.instruction = stripped.partition(":")[2].strip()
        elif stripped.lower().startswith("mesure"):
            lesson.time = stripped.partition(":")[2].strip()
        elif stripped.startswith("- "):
            body, time_sig = stripped[2:].strip(), lesson.time
            head, sep, rest = body.partition(":")
            if sep and "/" in head:  # « - 3/4 : b n | ... »
                time_sig, body = head.strip(), rest.strip()
            number = f"{lesson.number}.{len(lesson.exercises) + 1}"
            exercise = Exercise(number, time_sig, [SourceLine(body, where)])
            lesson.exercises.append(exercise)
        elif line.startswith(" ") and exercise is not None:
            exercise.lines.append(SourceLine(stripped, where))
        else:
            raise fail(
                f"ligne non comprise : « {stripped} » (un exercice commence par « - », sa 2e ligne par 2 espaces)"
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
