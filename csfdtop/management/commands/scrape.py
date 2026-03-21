from django.core.management.base import BaseCommand, CommandError

from csfdtop.scraping.scraping import run_scraping


class Command(BaseCommand):
    help = "Scrapes csfd.cz for top movies and saves them to the database"

    def handle(self, *args, **options):
        try:
            run_scraping()
        except Exception as e:
            raise CommandError(f"Scraping failed: {e}") from e
