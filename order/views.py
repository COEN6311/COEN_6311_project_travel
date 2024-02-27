import decimal
import json
from collections import defaultdict

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view

from order.constant import OrderStatus
from order.models import UserOrder, AgentOrder
from order.mq.mq_sender import send_auto_order_cancel
from product.models import CustomPackage
from user.models import User
from utils.number_util import generate_random_number, calculate_price_taxed
import logging

logger = logging.getLogger(__name__)


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
            package_id = data.get('package_id')
            user = request.user
            try:
                package = CustomPackage.objects.prefetch_related('packageitem_set').get(id=package_id)
            except CustomPackage.DoesNotExist:
                return JsonResponse({'result': False, 'errorMsg': 'Package not found'}, status=404)
            item_map = defaultdict(list)
            agent_map = defaultdict(User)
            current_time = timezone.now()

            # 获取关联的 Item
            package_items = package.packageitem_set.all()
            order_detail = []
            for packageItem in package_items:
                item = packageItem.item
                user_id = item.owner.id
                item_map[user_id].append(item)
                agent_map[user_id] = item.owner
                order_detail.append(packageItem.detail)
            user_order_price = calculate_price_taxed(package.price)
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
                status=OrderStatus.PENDING_PAYMENT.value  #
            )

            loop_count = 0
            # Adjust agent order information based on whether it is a user-built package.
            for user_id, items in item_map.items():
                loop_count += 1
                package_name = package.name if not package.is_user else 'User-created package'
                package_price_original = package.price if not package.is_user else sum(item.price for item in items)
                package_price_taxed = calculate_price_taxed(package_price_original)
                description = package.description if not package.is_user else 'User-created package'
                agent_order = AgentOrder.objects.create(
                    user_order=user_order,
                    name=package_name,
                    order_number=user_order_number,
                    agent_order_number=str(user_order_number) + str(loop_count),
                    order_details=order_detail,
                    description=description,
                    departure_date=departure_date,
                    end_date=end_date,
                    price=package_price_taxed,
                    user=user,
                    agent=agent_map.get(user_id, None),
                    phone=phone,
                    email=email,
                    status=OrderStatus.PENDING_PAYMENT.value  #
                )
            data = {
                'order_number': user_order.order_number,
                'order_time': str(user_order.create_time)
            }
            json_string = json.dumps(data)
            print(json_string)
            send_auto_order_cancel(json_string)
            logger.info("generate and order,order_number:"+user_order_number)
        return JsonResponse(
            {'result': True, 'data': {'order_number': user_order_number}, 'message': 'Order placed successfully'},
            status=201)

    except Exception as e:
        return JsonResponse({'result': False, 'errorMsg': 'system error'}, status=404)
