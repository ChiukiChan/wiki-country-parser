import pytest

from src.utils import (
    ACCENTS_RE,
    BRACKETS_RE,
    MULTISPACE_RE,
    PUNCT_BEFORE_RE,
    SENTENCE_SPLIT_RE,
    SQ_BRACKETS_RE,
)


def test_accents_re_removes_acute():
    s = "Амстерда\u0301м — город Нидерландов"
    out = ACCENTS_RE.sub("", s)
    assert out == "Амстердам — город Нидерландов"


@pytest.mark.parametrize(
    "src,expected",
    [
        ("Текст [3] дальше", "Текст  дальше"),
        ("Ссылка [ 12 ] и ещё [abc]", "Ссылка  и ещё "),
        ("Без скобок", "Без скобок"),
    ],
)
def test_sq_brackets_re_removes_square_bracket_chunks(src, expected):
    out = SQ_BRACKETS_RE.sub("", src)
    assert out == expected


def test_brackets_re_removes_only_non_nested_once():
    s = "A (x (y) z) B"
    # Один проход
    out_once = BRACKETS_RE.sub("", s)
    assert out_once == "A (x  z) B"
    # Множественные проходы
    prev, cur = None, s
    while prev != cur:
        prev = cur
        cur = BRACKETS_RE.sub("", cur)
    assert cur == "A  B"


@pytest.mark.parametrize(
    "src,expected",
    [
        ("Добрый , день !", "Добрый, день!"),
        ("Так писать ; Не надо :", "Так писать; Не надо:"),
        ("Да ? Нет ?", "Да? Нет?"),
    ],
)
def test_punct_before_re_strips_spaces_before_punct(src, expected):
    out = PUNCT_BEFORE_RE.sub(r"\1", src)
    assert out == expected


@pytest.mark.parametrize(
    "src,expected",
    [
        ("a  b\t c \n d", "a b c d"),
        ("  один   два   ", " один два "),
    ],
)
def test_multispace_re_collapses_whitespace(src, expected):
    out = MULTISPACE_RE.sub(" ", src)
    assert out == expected


def test_sentence_split_re_splits_on_sentence_boundaries():
    s = "Несколько. Предложений. Раздели! Пожалуйста?"
    parts = SENTENCE_SPLIT_RE.split(s)
    assert parts == ["Несколько.", "Предложений.", "Раздели!", "Пожалуйста?"]
