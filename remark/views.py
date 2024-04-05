from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view

from product.service.item_service import get_item_by_category_and_id
from product.service.package_service import service_refresh_redis_packages_with_items
from remark.models import Remark


# Create your views here.

@api_view(["POST"])
def add_remark(request):
    user = request.user
    user_id = user.id
    username = user.first_name + ' ' + user.last_name
    order_number = request.data.get('order_number', None)
    item_category = request.data.get('item_type', None)
    item_id = request.data.get('item_id', None)
    rating = request.data.get('rating', None)
    comment = request.data.get('comment', None)

    if not (user_id and username and order_number and item_category and item_id and rating):
        return JsonResponse({'result': False, 'errorMsg': 'Please fill in all required fields.'}, status=400)

    remark = Remark.create_or_update(
        user_id=user_id,
        user_name=username,
        order_number=order_number,
        item_category=item_category,
        item_id=item_id,
        rating=rating,
        comment=comment
    )

    # calculate remark
    item = get_item_by_category_and_id(item_category, item_id)
    if item is not None:
        avg_rating = Remark.objects.filter(item_category=item_category, item_id=item_id).aggregate(Avg('rating'))
        avg_rating_value = avg_rating['rating__avg']
        if avg_rating_value is not None:
            item.rating = avg_rating_value
            item.rating_count = Remark.objects.filter(item_category=item_category, item_id=item_id).count()

        item.save()

    service_refresh_redis_packages_with_items()
    return JsonResponse(
        {'result': True, 'message': 'Remark created successfully'},
        status=201)
