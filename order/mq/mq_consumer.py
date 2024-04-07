import json

import pika
from django.db import transaction

from order.constant import OrderStatus
from order.models import UserOrder, AgentOrder
from order.mq.get_connection import get_rabbitmq_connection
from order.mq.mq_sender import auto_order_cancel_queue, auto_order_notify_payment_queue
import logging

from order.service.order_service import send_order_notify_payment_email
from promotion.consumer.result_consumer import browse_notify_callback

logger = logging.getLogger(__name__)


def expire_order_callback(ch, method, properties, body):
    try:
        # data = '{"order_number": "92297759374073086834", "order_time": "2024-02-27 16:53:51.253304"}'
        logger.info("Received message from Queue 1:" + body.decode())
        parsed_data = json.loads(body.decode())
        order_number = parsed_data.get("order_number")

        user_order = UserOrder.objects.filter(order_number=order_number,
                                              status=OrderStatus.PENDING_PAYMENT.value).first()
        if not user_order:
            logger.info("order need not expire handle")
            return
        agent_orders = AgentOrder.objects.filter(user_order=user_order)
        with transaction.atomic():
            user_order.soft_delete()
            for agent_order in agent_orders:
                agent_order.soft_delete()
            logger.info("order expire handled,order:" + order_number)
    except Exception as e:
        logger.error(f"An error occurred: {e}")


def order_notify_payment_callback(ch, method, properties, body):
    try:
        logger.info("Received message from Queue Order Notify Payment:" + body.decode())
        parsed_data = json.loads(body.decode())
        order_number = parsed_data.get("order_number")
        email = parsed_data.get("email")

        user_order = UserOrder.objects.filter(order_number=order_number,
                                              status=OrderStatus.PENDING_PAYMENT.value).first()
        if not user_order:
            logger.info("order is deleted or paid")
            return
        send_order_notify_payment_email(order_number, email)
        logger.info(f"order notify payment handled, order: {order_number}, email: {email}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


# def callback2(ch, method, properties, body):
#     print("Received message from Queue 2:", body.decode())
#     # 处理队列2的消息

def start_consumer():
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        # channel.queue_declare(queue=auto_order_cancel_queue)
        channel.basic_consume(queue=auto_order_cancel_queue, on_message_callback=expire_order_callback, auto_ack=True)
        channel.basic_consume(queue=auto_order_notify_payment_queue, on_message_callback=order_notify_payment_callback,
                              auto_ack=True)
        channel.basic_consume(queue='flink-result', on_message_callback=browse_notify_callback,
                              auto_ack=True)
        # channel.queue_declare(queue='queue2')
        #
        # channel.basic_consume(queue='queue2', on_message_callback=callback2, auto_ack=True)
        logger.info('Consumer started. Waiting for messages...')

        channel.start_consuming()
    except Exception as e:
        logger.error("error:" + str(e))
