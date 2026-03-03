from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Film, Actor
from .utils import normalize_text


def search_view(request):
    query = request.GET.get("q", "")

    actor_results = []
    film_results = []

    if query:
        normalized_query = normalize_text(query)

        # Search Actors
        actors = Actor.objects.filter(name_normalized__contains=normalized_query)
        for actor in actors:
            actor_results.append({"name": actor.name, "id": actor.id})

        # Search Films
        films = Film.objects.filter(name_normalized__contains=normalized_query)
        for film in films:
            film_results.append({"name": film.name, "id": film.id, "year": film.year})

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"actors": actor_results, "films": film_results})

    return render(request, "csfdtop/index.html")


def film_detail(request, film_id):
    film = get_object_or_404(Film.objects.prefetch_related("actors"), id=film_id)
    return render(request, "csfdtop/film_detail.html", {"film": film})


def actor_detail(request, actor_id):
    actor = get_object_or_404(Actor.objects.prefetch_related("films"), id=actor_id)
    return render(request, "csfdtop/actor_detail.html", {"actor": actor})
