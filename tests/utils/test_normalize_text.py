import pytest

from csfdtop.utils import normalize_text


@pytest.mark.parametrize(
    "test_text, expected_result",
    [
        ("Český film", "cesky film"),
        ("", ""),
    ],
)
def test_normalize_text(test_text, expected_result):
    assert normalize_text(test_text) == expected_result
