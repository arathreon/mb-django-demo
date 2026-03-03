from django.core.management.base import BaseCommand

from csfdtop.scraping import run_scraping


class Command(BaseCommand):
    help = "Scrapes csfd.cz for top movies and saves them to the database"

    def handle(self, *args, **options):
        run_scraping()
