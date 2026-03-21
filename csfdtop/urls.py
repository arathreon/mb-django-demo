from django.urls import path

from csfdtop.views import search_view, search_api, film_detail, actor_detail

app_name = "csfdtop"
urlpatterns = [
    path("", search_view, name="index"),
    path("api/search/", search_api, name="search_api"),
    path("film/<int:film_id>/", film_detail, name="film_detail"),
    path("actor/<int:actor_id>/", actor_detail, name="actor_detail"),
]
