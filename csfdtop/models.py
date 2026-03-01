from django.db import models

from csfdtop.utils import get_name_year_hash


class Actor(models.Model):
    # Assuming an actor's name is unique (for simplicity)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Film(models.Model):
    # Assuming name and year combination is unique
    name = models.CharField(max_length=255)
    year = models.PositiveSmallIntegerField()
    name_year_hash = models.CharField(max_length=64, unique=True)
    actors = models.ManyToManyField(Actor, related_name="films")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "year"], name="unique_film_name_year"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.year})"

    def save(self, *args, **kwargs):
        self.name_year_hash = get_name_year_hash(self.name, self.year)
        super().save(*args, **kwargs)
