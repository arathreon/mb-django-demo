import pytest

from csfdtop.scraping import create_actor_and_add_normalized_name
from csfdtop.models import Actor


@pytest.mark.parametrize(
    "tested_string, expected_result",
    [
        ("Alžběta Tůmová Nováková", "alzbeta tumova novakova"),
        ("Jean-Claude Van Damme", "jean-claude van damme"),
    ],
)
def test_create_actor_and_add_normalized_name(tested_string, expected_result):
    actor = create_actor_and_add_normalized_name(tested_string)

    assert isinstance(actor, Actor)
    assert actor.name == tested_string
    assert actor.name_normalized == expected_result
    # Ensure it's not saved to DB yet
    assert actor.pk is None
