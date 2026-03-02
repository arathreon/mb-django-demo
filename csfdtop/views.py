from django.shortcuts import render
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
