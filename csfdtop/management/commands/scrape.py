from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Scrapes csfd.cz for top movies and saves them to the database"

    def handle(self, *args, **options):
        self.stdout.write("Successfully started command!")
