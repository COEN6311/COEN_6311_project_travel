import decimal
import json
import threading
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view

from product.service.item_service import get_item_serializer, get_json_structure_by_item
from order import task
from order.constant import OrderStatus
from order.models import UserOrder, AgentOrder, Payment
from order.mq.mq_sender import send_auto_order_notify_payment, send_auto_order_cancel
from order.serializers import UserOrderSerializer, AgentOrderSerializer
from order.service.order_service import handle_payment, calculate_prices, send_order_payment_email, \
    get_order_status_by_date_span
from product.models import CustomPackage
from product.serializers import CustomPackageSerializer
from promotion.etl import async_order_payment_data
from user.models import User
from utils.constant import user_create_package_name
from utils.number_util import generate_random_number, calculate_price_taxed
import logging

logger = logging.getLogger(__name__)


@api_view(["POST"])
def payment_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_number = data.get('order_number')
            # card_number = data.get('card_number')
            # security_code = data.get('security_code')
            amount = data.get('amount')
            user = request.user
            if not all([order_number, amount]):
                return JsonResponse({'result': False, 'errorMsg': 'One or more required fields are missing.'},
                                    status=400)

            user_order = UserOrder.objects.filter(order_number=order_number,
                                                  status=OrderStatus.PENDING_PAYMENT.value).first()
            if not user_order:
                logger.info("order need not payment handle,order:" + order_number)
                return JsonResponse({'result': False,
                                     'errorMsg': 'Order does not exist or the order has already been paid.'},
                                    status=400)
            if calculate_price_taxed(user_order.price) != Decimal(amount).quantize(Decimal('0.01')):
                return JsonResponse({'result': False, 'message': 'Invalid payment amount.'}, status=400)
            agent_orders = AgentOrder.objects.filter(user_order=user_order)
            # pending payment transfer to pending departure or travelling
            if not handle_payment(0, 0, amount):
                return JsonResponse({'result': False, 'message': 'payment failed.'}, status=400)
            payment_time = timezone.now()
            order_status = OrderStatus.PENDING_DEPARTURE.value
            # if payment_time.date() == user_order.departure_date:
            #     order_status = OrderStatus.TRAVELING.value
            with transaction.atomic():
                payment = Payment.objects.create(
                    order=user_order,
                    user=user,
                    amount=amount,
                    payment_time=payment_time
                )
                user_order.status = order_status
                user_order.payment_time = payment_time
                user_order.save()
                for agent_order in agent_orders:
                    agent_order.status = order_status
                    agent_order.payment_time = payment_time
                    agent_order.save()
                logger.info("order payment successfully:" + order_number)
            send_order_payment_email(order_number, user.email)
            return JsonResponse({'result': True, 'message': 'Order payment successfully.'})
        except json.JSONDecodeError:
            return JsonResponse({'result': False, 'errorMsg': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            logger.exception("An error occurred: %s", e)
            return JsonResponse({'result': False, 'errorMsg': str(e)}, status=500)
    else:
        return JsonResponse({'result': False, 'errorMsg': 'Only POST requests are allowed.'}, status=405)


# Create your views here.
@api_view(["POST"])
def place_order(request):
    try:
        with transaction.atomic():
            data = json.loads(request.body.decode('utf-8'))
            departure_date = data.get('departure_date')
            end_date = data.get('end_date')
            email = data.get('email')
            phone = data.get('phone')
            package_id = data.get('packageId')
            user = request.user
            try:
                package = CustomPackage.objects.prefetch_related('packageitem_set').get(id=package_id)
            except CustomPackage.DoesNotExist:
                return JsonResponse({'result': False, 'errorMsg': 'Package not found'}, status=404)
            item_map = defaultdict(list)
            agent_map = defaultdict(User)
            current_time = timezone.now()

            # get Item
            package_items = package.packageitem_set.all()
            order_detail = []
            user_order_items = []
            for packageItem in package_items:
                item = packageItem.item
                user_id = item.owner.id
                item_map[user_id].append(item)
                agent_map[user_id] = item.owner
                order_detail.append(packageItem.detail)
                user_order_items.append(get_json_structure_by_item(item))
            user_order_price = package.price
            user_order_number = generate_random_number()
            user_order = UserOrder.objects.create(
                name=package.name,
                order_number=user_order_number,
                order_details=order_detail,
                description=package.description,
                departure_date=departure_date,
                end_date=end_date,
                price=user_order_price,
                user=user,
                phone=phone,
                email=email,
                package_id=package.id,
                items=user_order_items,
                is_agent_package=not package.is_user,
                status=OrderStatus.PENDING_PAYMENT.value  #
            )

            loop_count = 0
            # Adjust agent order information based on whether it is a user-built package.
            for user_id, items in item_map.items():
                loop_count += 1
                package_name = package.name if not package.is_user else user_create_package_name
                package_price_original = package.price if not package.is_user else sum(item.price for item in items)
                flight_price, activity_price, hotel_price = calculate_prices(items)
                # package_price_taxed = calculate_price_taxed(package_price_original)
                description = package.description if not package.is_user else user_create_package_name
                agent_order_items = []
                for item in items:
                    agent_order_items.append(get_json_structure_by_item(item))
                agent_order = AgentOrder.objects.create(
                    user_order=user_order,
                    name=package_name,
                    order_number=user_order_number,
                    agent_order_number=str(user_order_number) + str(loop_count),
                    order_details=order_detail,
                    description=description,
                    departure_date=departure_date,
                    end_date=end_date,
                    price=package_price_original,
                    user=user,
                    agent=agent_map.get(user_id, None),
                    phone=phone,
                    email=email,
                    items=agent_order_items,
                    package_id=package.id,
                    flight_price=flight_price,
                    hotel_price=hotel_price,
                    activity_price=activity_price,
                    is_agent_package=not package.is_user,
                    status=OrderStatus.PENDING_PAYMENT.value  #
                )
            data = {
                'order_number': user_order.order_number,
                'order_time': str(user_order.create_time),
                'email': user_order.email
            }
            json_string = json.dumps(data)
            send_auto_order_cancel(json_string)
            send_auto_order_notify_payment(json_string)
            async_order_payment_data(package_items, request.user.id)
            logger.info("generate and order,order_number:" + user_order_number)
        return JsonResponse(
            {'result': True, 'data': {
                'order_number': user_order_number,
                'amount': float(calculate_price_taxed(user_order_price))
            }, 'message': 'Order placed successfully'},
            status=201)

    except Exception as e:
        logger.exception("An error occurred: %s", e)
        return JsonResponse({'result': False, 'errorMsg': 'system error'}, status=404)


@api_view(['GET'])
def view_orders(request):
    try:
        owner = request.user
        is_user = not owner.is_agent
        if is_user:
            orders = UserOrder.objects.filter(user=owner).order_by('-id')
            serializer = UserOrderSerializer(orders, many=True)
            response_data = {
                'result': 'success',
                'message': 'Orders retrieved successfully',
                'errorMsg': None,
                'data': serializer.data
            }
        else:
            orders = AgentOrder.objects.filter(agent=owner).order_by('-id')
            serializer = AgentOrderSerializer(orders, many=True)
            response_data = {
                'result': 'success',
                'message': 'Orders retrieved successfully',
                'errorMsg': None,
                'data': serializer.data
            }
        log_message = f"View orders for user {owner.id}: {len(serializer.data)}"
        logger.info(log_message)
        return JsonResponse(response_data)
    except Exception as e:
        logger.exception("An error occurred: %s", e)
        return JsonResponse({'result': False, 'errorMsg': 'system error'}, status=404)


@api_view(['POST'])
def cancel_order(request):
    order_number = request.data.get('order_number')
    if not order_number:
        return JsonResponse({'result': False, 'errorMsg': 'Please provide order number', 'message': "", 'data': None},
                            status=status.HTTP_400_BAD_REQUEST)
    try:
        user_order = UserOrder.objects.prefetch_related('agent_orders').get(order_number=order_number)
        if user_order.status == OrderStatus.CANCELLED.value:
            logger.info(f'Order {order_number} is already cancelled')
            return JsonResponse({'result': True, 'message': 'Order is already cancelled'}, status=status.HTTP_200_OK)

        with transaction.atomic():
            user_order.status = OrderStatus.CANCELLED.value
            user_order.save()

            for agent_order in user_order.agent_orders.all():
                agent_order.status = OrderStatus.CANCELLED.value
                agent_order.save()
        logger.info(f'Order {order_number} successfully cancelled')
        return JsonResponse({'result': True, 'message': 'Order successfully cancelled'}, status=status.HTTP_200_OK)
    except UserOrder.DoesNotExist:
        logger.error(f'Order {order_number} does not exist')
        return JsonResponse({'result': False, 'errorMsg': 'Order does not exist', 'message': "", 'data': None},
                            status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception('An error occurred while cancelling the order')
        return JsonResponse({'result': False, 'errorMsg': str(e), 'message': "", 'data': None},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def modify_order(request):
    order_number = request.data.get('order_number')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    if not order_number:
        return JsonResponse({'result': False, 'errorMsg': 'Please provide order number', 'message': "", 'data': None},
                            status=status.HTTP_400_BAD_REQUEST)
    try:
        user_order = UserOrder.objects.prefetch_related('agent_orders').get(order_number=order_number)
        if user_order.status == OrderStatus.CANCELLED.value:
            logger.info(f'Order {order_number} is already cancelled')
            return JsonResponse({'result': True, 'message': 'OOrder is currently canceled and cannot be modified.'},
                                status=status.HTTP_200_OK)
        if user_order.status == OrderStatus.PENDING_PAYMENT.value:
            order_status = OrderStatus.PENDING_PAYMENT.value
        else:
            order_status = get_order_status_by_date_span(start_date, end_date)
        with transaction.atomic():
            user_order.status = order_status
            user_order.departure_date = start_date
            user_order.end_date = end_date
            user_order.save()

            for agent_order in user_order.agent_orders.all():
                agent_order.departure_date = start_date
                agent_order.end_date = end_date
                agent_order.status = order_status
                agent_order.save()
        logger.info(f'Order {order_number} successfully modified')
        return JsonResponse({'result': True, 'message': 'Order successfully modified'}, status=status.HTTP_200_OK)
    except UserOrder.DoesNotExist:
        logger.error(f'Order {order_number} does not exist')
        return JsonResponse({'result': False, 'errorMsg': 'Order does not exist', 'message': "", 'data': None},
                            status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception('An error occurred while modified the order')
        return JsonResponse({'result': False, 'errorMsg': str(e), 'message': "", 'data': None},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def agent_report(request):
    try:
        owner = request.user
        is_agent = owner.is_agent
        if not is_agent:
            return JsonResponse(
                {'result': False, 'errorMsg': 'Permission denied. Only agents can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN)
        else:
            orders = AgentOrder.objects.filter(agent=owner, is_delete=False)
            total_orders_count = len(orders)
            # Calculate count of orders with status=9
            canceled_orders_count = sum(1 for order in orders if order.status == OrderStatus.CANCELLED.value)
            # Filter out orders with status not equal to 9 and generate a new list
            filtered_orders = [order for order in orders if order.status != OrderStatus.CANCELLED.value]
            total_flight_revenue = sum(order.flight_price for order in filtered_orders)
            total_hotel_revenue = sum(order.hotel_price for order in filtered_orders)
            total_activity_revenue = sum(order.activity_price for order in filtered_orders)
            total_revenue = sum(order.price for order in filtered_orders)
            success_order_count = total_orders_count - canceled_orders_count
            success_rate = round((success_order_count / total_orders_count) * 100, 1) if total_orders_count > 0 else 0

            top_packages = AgentOrder.objects.filter(agent=owner, is_delete=False, is_agent_package=1) \
                               .exclude(status=9).values('package_id').annotate(
                package_count=Count('package_id')).order_by('-package_count')[:3]
            top_packages_ids = [package['package_id'] for package in top_packages]
            top_packages_details = CustomPackage.objects.filter(id__in=top_packages_ids)
            response_data = {
                'result': 'success',
                'message': 'Report retrieved successfully',
                'errorMsg': None,
                'data': {
                    'report_detail': {
                        'total_order_count': total_orders_count,
                        'canceled_order_count': canceled_orders_count,
                        'success_order_count': success_order_count,
                        'success_rate': success_rate,
                        'total_revenue': float(total_revenue),
                        'total_flight_revenue': float(total_flight_revenue),
                        'total_hotel_revenue': float(total_hotel_revenue),
                        'total_activity_revenue': float(total_activity_revenue)
                    },
                    'top_package': CustomPackageSerializer(top_packages_details, many=True).data

                }
            }
            # logger.info(log_message)
        return JsonResponse(response_data)
    except Exception as e:
        logger.exception("An error occurred: %s", e)
        return JsonResponse({'result': False, 'errorMsg': 'system error'}, status=404)
