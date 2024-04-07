import json
import time

from order.mq.get_connection import get_rabbitmq_connection

def send_browse_data_to_mq(item, item_type, userId):
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    queue_name = "flink-source"
    channel.queue_declare(queue=queue_name, durable=True)
    message_dict = {
        "itemId": item.id,
        "category": item_type,
        "type": 1,
        "userId": userId,
        "timestamp": int(time.time() * 1000)
    }
    # {"timestamp": 1712180317679, "category": "Category A", "itemId": 1001, "userId": 1, "type": 1}

    message = json.dumps(message_dict)
    print(message)
    # delay 15 min
    channel.basic_publish(exchange='', routing_key=queue_name, body=message)

    print(" [x] Sent browse message:", message)
    connection.close()
