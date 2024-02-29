from django.core.management import BaseCommand
import threading
from order.mq.mq_consumer import start_consumer
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Starts the order consumer'

    def handle(self, *args, **options):
        logger.info('Starting order consumer')
        print("Starts the order consumer!!!")

        # 定义一个新的线程
        consumer_thread = threading.Thread(target=start_consumer)

        # 启动线程
        consumer_thread.start()
