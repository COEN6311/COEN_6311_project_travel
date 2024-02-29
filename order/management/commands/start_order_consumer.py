from django.core.management import BaseCommand

from order.mq.mq_consumer import start_consumer, logger


class Command(BaseCommand):
    help = 'Starts the order consumer'

    def handle(self, *args, **options):
        logger.info("Starts the order consumer!!!")
        start_consumer()
