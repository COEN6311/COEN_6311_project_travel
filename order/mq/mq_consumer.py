# import pika
# import json
# import time
#
# from order.mq.get_connection import connection
#
#
# def callback(ch, method, properties, body):
#     print("Received message:", body.decode())
#     # 这里可以添加处理订单的逻辑
#
#
# def start_order_consumer():
#     channel = connection.channel()
#
#     # 声明一个延迟队列
#     channel.queue_declare(queue='delayed_orders', arguments={'x-message-ttl': 900000})  # 15分钟，单位是毫秒
#
#     # 绑定队列和回调函数
#     channel.basic_consume(queue='delayed_orders', on_message_callback=callback, auto_ack=True)
#
#     print('Order consumer started. Waiting for messages...')
#     channel.start_consuming()