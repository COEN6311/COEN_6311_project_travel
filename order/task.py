import datetime

from celery import shared_task
import logging

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from order.constant import OrderStatus
from order.models import UserOrder

logger = logging.getLogger(__name__)


@shared_task
def schedule_task():
    logger.info("schedule_task run")


@shared_task
def change_order_status_task():
    try:
        # Get today's date
        today = datetime.date.today()

        # Query all user orders that are not soft deleted, with departure date today, and status pending departure
        pending_travel_user_orders = UserOrder.objects.filter(departure_date=today,
                                                              status=OrderStatus.PENDING_DEPARTURE.value,
                                                              is_delete=False).prefetch_related('agent_orders')
        count = 0
        # Change user order status to traveling
        for user_order in pending_travel_user_orders:
            with transaction.atomic():
                user_order.status = OrderStatus.TRAVELING.value
                user_order.save()

                # Change corresponding agent orders status to traveling
                for agent_order in user_order.agent_orders.all():
                    agent_order.status = OrderStatus.TRAVELING.value
                    agent_order.save()
                count += 1
            # Log the status change
            logger.info(
                f"Order number {user_order.order_number} has changed status from PENDING_DEPARTURE to TRAVELING")
        logger.info(f"Total orders changed status from PENDING_DEPARTURE to TRAVELING: {count}")

        # Query all user orders that are not soft deleted, with end_date earlier than today and status traveling
        travalling_user_orders = UserOrder.objects.filter(end_date__lt=today, status=OrderStatus.TRAVELING.value,
                                                          is_delete=False).prefetch_related('agent_orders')

        count = 0
        # Change user order status to travelled
        for user_order in travalling_user_orders:
            with transaction.atomic():
                user_order.status = OrderStatus.COMPLETED.value
                user_order.save()

                # Change corresponding agent orders status to travelled
                for agent_order in user_order.agent_orders.all():
                    agent_order.status = OrderStatus.COMPLETED.value
                    agent_order.save()
                count += 1
            # Log the status change for each order
            logger.info(f"Order number {user_order.order_number} has changed status from TRAVELING to COMPLETE")

        # Log the total count of orders whose status has been changed
        logger.info(f"Total orders changed status from TRAVELING to TRAVELLED: {count}")

        return Response({"message": "Order status changed successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        # Log exception information or perform other actions such as sending alerts
        logger.error(f"An exception occurred while modifying order status: {str(e)}")
        return Response({"message": "Order status changed successfully"}, status=status.HTTP_200_OK)
