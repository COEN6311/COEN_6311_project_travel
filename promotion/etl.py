import threading
import time
import logging

from order.mq.get_connection import get_rabbitmq_connection
from promotion.sender.brower_sender import send_browse_data_to_mq
from promotion.sender.payment_sender import send_order_data_to_mq

logger = logging.getLogger(__name__)


def async_process_browse_data(item, item_type, userId):
    print(f"Running in thread: {threading.current_thread().name}")

    browse_data_thread = threading.Thread(target=process_browse_data,
                                          args=(item, item_type, userId))
    browse_data_thread.start()


def process_browse_data(item, item_type, userId):
    send_browse_data_to_mq(item, item_type, userId)


def async_order_payment_data(packageItems, userId):
    payment_data_thread = threading.Thread(target=process_order_data,
                                           args=(packageItems, userId))
    payment_data_thread.start()


def process_order_data(packageItems, userId):
    send_order_data_to_mq(packageItems, userId)
