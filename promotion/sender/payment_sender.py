import json
import logging
import time

from order.mq.get_connection import get_rabbitmq_connection

logger = logging.getLogger(__name__)


def send_order_data_to_mq(packageItems, userId):
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    queue_name = "flink-source"
    channel.queue_declare(queue=queue_name, durable=True)
    for packageItem in packageItems:
        message_dict = {
            "itemId": packageItem.item_object_id,
            "category": packageItem.type,
            "type": 2,
            "userId": userId,
            "timestamp": int(time.time() * 1000)
        }
        # {"timestamp": 1712180317679, "category": "Category A", "itemId": 1001, "userId": 1, "type": 2}

        message = json.dumps(message_dict)
        logger.info('send order data to mq:' + message)
        # delay 15 min
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)

    connection.close()
