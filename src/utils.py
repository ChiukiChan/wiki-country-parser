import re

ACCENTS_RE = re.compile(r"[\u0301\u0341\u00B4]")  # Ударения/диакритики
SQ_BRACKETS_RE = re.compile(r"\[[^\]]*\]")  # Cсылки на литературу [ 3 ][2]
BRACKETS_RE = re.compile(r"\([^()]*\)")  # (Информация в круглых скобках)
PUNCT_BEFORE_RE = re.compile(r"\s+([,.;:!?])")  # пробелы перед пунктуацией
MULTISPACE_RE = re.compile(r"\s+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def clean_name(s: str) -> str:
    s = SQ_BRACKETS_RE.sub("", s)
    s = MULTISPACE_RE.sub(" ", s).strip()
    return s


def clean_desc(s: str) -> str:
    s = ACCENTS_RE.sub("", s)
    s = SQ_BRACKETS_RE.sub("", s)

    # Для удаления вложенных круглых скобок
    prev = None
    while prev != s:
        prev = s
        s = BRACKETS_RE.sub("", s)

    s = PUNCT_BEFORE_RE.sub(r"\1", s)
    s = MULTISPACE_RE.sub(" ", s).strip()
    parts = SENTENCE_SPLIT_RE.split(s, maxsplit=2)
    s = " ".join(parts[:2])
    return s
