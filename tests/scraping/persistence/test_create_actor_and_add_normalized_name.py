import pytest

from csfdtop.scraping.parsing import ActorInfo
from csfdtop.scraping.persistence import create_actor_and_add_normalized_name
from csfdtop.models import Actor


@pytest.mark.parametrize(
    "tested_actor_info, expected_result",
    [
        (ActorInfo(csfd_id=1, name="Alžběta Tůmová Nováková"), "alzbeta tumova novakova"),
        (ActorInfo(csfd_id=1, name="Jean-Claude Van Damme"), "jean-claude van damme"),
    ],
)
def test_create_actor_and_add_normalized_name(tested_actor_info, expected_result):
    actor = create_actor_and_add_normalized_name(tested_actor_info)

    assert isinstance(actor, Actor)
    assert actor.csfd_id == tested_actor_info.csfd_id
    assert actor.name == tested_actor_info.name
    assert actor.name_normalized == expected_result
    # Ensure it's not saved to DB yet
    assert actor.pk is None
