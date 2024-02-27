import sys

from django.http import JsonResponse
import pika
import json

from order.mq.get_connection import get_rabbitmq_connection

auto_order_cancel_delay = 10
auto_order_cancel_exchange = 'auto_order_cancel_exchange_1'
auto_order_cancel_queue = 'auto_order_cancel_queue_1'


def send_auto_order_cancel(message):
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.exchange_declare(
        exchange=auto_order_cancel_exchange,
        exchange_type='x-delayed-message',
        arguments={'x-delayed-type': 'direct'}  # 设置延迟消息的类型，这里设为 direct
    )
    channel.queue_declare(queue=auto_order_cancel_queue, durable=True)
    channel.queue_bind(exchange=auto_order_cancel_exchange, queue=auto_order_cancel_queue,
                       routing_key=auto_order_cancel_queue)

    properties = pika.BasicProperties(
        headers={'x-delay': auto_order_cancel_delay * 1000}
    )
    # delay 15 min
    channel.basic_publish(exchange=auto_order_cancel_exchange, routing_key=auto_order_cancel_queue, body=message,
                          properties=properties)

    print(" [x] Sent delayed message:", message)

    # 关闭连接
    connection.close()
