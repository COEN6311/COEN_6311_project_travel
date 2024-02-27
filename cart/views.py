import decimal


from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from rest_framework.decorators import api_view
from django.http import JsonResponse
from cart.models import CartItem, Cart
from cart.serializers import CartSerializer
from product.models import PackageItem, CustomPackage
from product.serializers import CustomPackageSerializer
from product.views import get_model_by_item_type, insert_package
from user.models import User
from utils.constant import tax_rate

import logging
logger = logging.getLogger(__name__)

@api_view(["POST"])
def add_item(request):
    if request.method == 'POST':
        try:
            data = request.data
            items = data.get('items', [])
            user = request.user  # 获取当前用户实例
            cart, created = Cart.objects.get_or_create(user=user)

            for item_data in items:
                item_type = item_data.get('type')
                item_id = item_data.get('id')
                quantity = item_data.get('number')

                # 创建购物车项并将购物车实例分配给 cart 字段
                cart_item = CartItem.objects.create(
                    cart=cart,
                    item_content_type=ContentType.objects.get_for_model(get_model_by_item_type(item_type)),
                    item_object_id=item_id,
                    quantity=quantity,
                    type=item_type
                )
            cart_serializer = CartSerializer(cart)
            cart_data = cart_serializer.data

            response_data = {
                'result': 'true',
                'message': 'Items added to cart successfully',
                'data': {'cart': cart_data}
            }
            return JsonResponse(response_data)
        except IntegrityError:
            return JsonResponse({'result': 'false', 'errorMsg': 'Do not add the same item repeatedly'}, status=404)
    else:
        return JsonResponse({'result': 'false', 'errorMsg': 'Only POST requests are allowed'}, status=404)


@api_view(["POST"])
def delete_item(request):
    if request.method == 'POST':
        data = request.data
        cart_item_id = data.get('cartItemId')

        if not request.user.is_authenticated:
            return JsonResponse({'result': 'false', 'errorMsg': 'User is not authenticated'}, status=401)

        # 获取当前用户的购物车
        user_cart = Cart.objects.filter(user=request.user).first()
        if not user_cart:
            return JsonResponse({'result': 'false', 'errorMsg': 'Cart not found for current user'}, status=404)

        try:
            cart_item = CartItem.objects.get(id=cart_item_id, cart=user_cart)
        except CartItem.DoesNotExist:
            return JsonResponse(
                {'result': 'false', 'errorMsg': 'CartItem not found or does not belong to current user'}, status=404)
        cart_item.delete()
        response_data = {
            'result': 'true',
            'data': {'cart': getCartContent(request.user)},
            'message': 'delete success'
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({'result': 'false', 'errorMsg': 'Only POST requests are allowed'}, status=405)


@api_view(["POST"])
def cartCheckout(request):
    try:
        with transaction.atomic():
            cart = Cart.objects.filter(user=request.user).first()
            if not cart:
                return JsonResponse({'result': 'false', 'errorMsg': 'Cart does not exist'}, status=404)
            # Retrieve cart items
            cart_items = CartItem.objects.filter(cart=cart)
            if not cart_items:
                return JsonResponse({'result': 'false', 'errorMsg': 'Cart is empty'}, status=404)

            package_items = []
            for cart_item in cart_items:
                item_data = {
                    "number": cart_item.quantity,
                    "type": cart_item.type,
                    "id": cart_item.item_object_id
                }
                package_items.append(item_data)
            # Bulk create package items
            # todo   the package null name and null description and null feature
            custom_package = insert_package({}, request.user, package_items)
            # Clear cart items
            cart_items.delete()
            # Serialize custom_package
            data = checkoutJsonInformation(custom_package)
        return JsonResponse({'result': 'true', 'data': data})
    except User.DoesNotExist:
        return JsonResponse({'result': 'false', 'errorMsg': 'User does not exist'}, status=404)
    except Cart.DoesNotExist:
        return JsonResponse({'result': 'false', 'errorMsg': 'Cart does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'result': 'false', 'errorMsg': 'system error'}, status=404)


@api_view(["POST"])
def packageCheckout(request):
    try:
        # Get packageId from request data
        package_id = request.data.get('packageId')
        # Retrieve the custom package using packageId
        custom_package = CustomPackage.objects.filter(id=package_id).first()
        # Check if custom package exists
        if not custom_package:
            return JsonResponse({'result': 'false', 'errorMsg': 'Custom package does not exist'}, status=404)
        # Serialize custom_package
        data = checkoutJsonInformation(custom_package)
        return JsonResponse({'result': 'true', 'data': data})
    except Exception as e:
        return JsonResponse({'result': 'false', 'errorMsg': 'System error'}, status=404)


@api_view(["GET"])
def query_by_user(request):
    try:
        response_data = {
            'result': 'true',
            'data': {'cart': getCartContent(request.user)}
        }
        return JsonResponse(response_data)
    except User.DoesNotExist:
        return JsonResponse({'result': 'false', 'errorMsg': 'User does not exist'}, status=404)
    except Cart.DoesNotExist:
        return JsonResponse({'result': 'false', 'errorMsg': 'Cart does not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'result': 'false', 'errorMsg': 'system error'}, status=404)


def getCartContent(user):
    cart = Cart.objects.filter(user=user).first()
    cart_serializer = CartSerializer(cart)
    cart_data = cart_serializer.data
    return cart_data


def checkoutJsonInformation(custom_package):
    serialized_package = CustomPackageSerializer(custom_package).data
    subtotal = custom_package.price
    taxes = (subtotal * decimal.Decimal(tax_rate)).quantize(decimal.Decimal('0.01'))
    total = (subtotal + taxes).quantize(decimal.Decimal('0.01'))
    data = {
        'Subtotal': subtotal,
        'Taxes': taxes,
        'Total': total,
        'package_items': serialized_package
    }
    return data
