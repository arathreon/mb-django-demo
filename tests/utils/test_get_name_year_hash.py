from csfdtop.utils import get_name_year_hash


def test_get_name_year_hash():
    assert (
        get_name_year_hash("some_test_string", "1994")
        == "5dee9fde179bbe29bb4774962a535203b60dacf4920c1b2901527e1faaf71628"
    )
