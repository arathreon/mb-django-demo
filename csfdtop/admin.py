from django.contrib import admin

from csfdtop.models import Film, Actor


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "csfd_id")
    search_fields = ("name", "name_normalized")
    list_filter = ("year",)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ("name", "csfd_id")
    search_fields = ("name", "name_normalized")
