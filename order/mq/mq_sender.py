from django.http import JsonResponse
import pika
import json

from order.mq.get_connection import connection

auto_order_cancel_delay = 15
auto_order_cancel_exchange = 'auto_order_cancel_exchange'
auto_order_cancel_queue = 'auto_order_cancel_queue'


def send_auto_order_cancel(message):
    channel = connection.channel()

    channel.exchange_declare(exchange=auto_order_cancel_exchange, exchange_type='direct')
    channel.queue_declare(queue=auto_order_cancel_queue, durable=True)
    channel.queue_bind(exchange=auto_order_cancel_exchange, queue=auto_order_cancel_queue, routing_key='')

    properties = pika.BasicProperties(
        headers={'x-delay': auto_order_cancel_delay * 1000}
    )
    # delay 15 min
    channel.basic_publish(exchange=auto_order_cancel_exchange, routing_key='', body=message, properties=properties)

    print(" [x] Sent delayed message:", message)

    # 关闭连接
    connection.close()
