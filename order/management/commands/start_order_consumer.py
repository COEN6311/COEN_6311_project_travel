from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Starts the order consumer'

    def handle(self, *args, **options):
        print("Starts the order consumer!!!")
