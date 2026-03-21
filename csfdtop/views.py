from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Film, Actor
from .utils import normalize_text


def search_view(request):
    return render(request, "csfdtop/index.html")


def search_api(request):
    query = request.GET.get("q", "").strip()
    if not query or len(query) < 3:
        return JsonResponse({"actors": [], "films": []})

    normalized_query = normalize_text(query)

    actor_results = list(Actor.objects.filter(name_normalized__contains=normalized_query).values("id", "name")[:50])
    film_results = list(
        Film.objects.filter(name_normalized__contains=normalized_query).values("name", "id", "year")[:50]
    )

    return JsonResponse({"actors": actor_results, "films": film_results})


def film_detail(request, film_id):
    film = get_object_or_404(Film.objects.prefetch_related("actors"), id=film_id)
    return render(request, "csfdtop/film_detail.html", {"film": film})


def actor_detail(request, actor_id):
    actor = get_object_or_404(Actor.objects.prefetch_related("films"), id=actor_id)
    return render(request, "csfdtop/actor_detail.html", {"actor": actor})
