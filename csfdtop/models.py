from django.db import models

from csfdtop.utils import normalize_text


class Actor(models.Model):
    # Using csfd_id to uniquely identify the actor
    csfd_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    name_normalized = models.CharField(max_length=255, editable=False)

    def save(self, *args, **kwargs):
        # save isn't called for update, bulk operations, etc., we need to handle normalization manually
        self.name_normalized = normalize_text(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Film(models.Model):
    # Using csfd_id to uniquely identify the film
    csfd_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    name_normalized = models.CharField(max_length=255, editable=False)
    year = models.PositiveSmallIntegerField()
    actors = models.ManyToManyField(Actor, related_name="films")

    def __str__(self):
        return f"{self.name} ({self.year})"

    def save(self, *args, **kwargs):
        # save isn't called for update, bulk operations, etc., we need to handle normalization manually
        self.name_normalized = normalize_text(self.name)
        super().save(*args, **kwargs)
