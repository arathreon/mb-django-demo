import pytest

from csfdtop.models import Actor
from csfdtop.scraping.parsing import ActorInfo
from csfdtop.scraping.persistence import get_existing_actors


@pytest.mark.django_db
def test_get_existing_actors_ok():
    Actor.objects.create(csfd_id=1, name="Will Smith", name_normalized="will smith")
    Actor.objects.create(csfd_id=3, name="Arnold Schwarzenegger", name_normalized="arnold schwarzenegger")

    test_input = [ActorInfo(csfd_id=1, name="Will Smith"), ActorInfo(csfd_id=2, name="Ryan Gosling")]

    assert get_existing_actors(test_input) == {1}
