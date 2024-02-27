import pika

from order.mq.get_connection import get_rabbitmq_connection
from order.mq.mq_sender import auto_order_cancel_queue


def callback1(ch, method, properties, body):
    print("Received message from Queue 1:", body.decode())
    # 处理队列1的消息


# def callback2(ch, method, properties, body):
#     print("Received message from Queue 2:", body.decode())
#     # 处理队列2的消息

def start_consumer():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    # 声明队列1
    # channel.queue_declare(queue=auto_order_cancel_queue)
    # 绑定队列1和回调函数1
    channel.basic_consume(queue=auto_order_cancel_queue, on_message_callback=callback1, auto_ack=True)
    # 声明队列2
    # channel.queue_declare(queue='queue2')
    #
    # # 绑定队列2和回调函数2
    # channel.basic_consume(queue='queue2', on_message_callback=callback2, auto_ack=True)
    print('Consumer started. Waiting for messages...')

    channel.start_consuming()
