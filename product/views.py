import json

from django.db import transaction
from django.db.models import Q, Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from cart.cart_service import delete_cart_item
from order.models import UserOrder
from user.customPermission import IsAgentPermission
from utils.constant import user_create_package_name
from .serializers import FlightTicketSerializer, HotelSerializer, CustomPackageSerializer, ActivitySerializer
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from .models import CustomPackage, PackageItem, FlightTicket, Hotel, User, Activity, soft_delete_package_item
from .service.package_service import get_packages_with_items, refresh_redis_packages_with_items, \
    update_related_packages_price_by_item
from .utils import get_item_detail


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10


# Function to get model and serializer based on type
def get_model_and_serializer(type_param):
    if type_param == '1':
        return FlightTicket, FlightTicketSerializer
    elif type_param == '2':
        return Hotel, HotelSerializer
    elif type_param == '3':
        return Activity, ActivitySerializer
    else:
        return None, None


def get_model_by_item_type(item_type):
    if item_type == 1:
        return FlightTicket
    elif item_type == 2:
        return Hotel
    elif item_type == 3:
        return Activity
    else:
        # Raise an exception if the type is not expected
        raise ValueError(f"Invalid item type {item_type}")


# Function to get all models and their serializers
def get_all_models_and_serializers():
    return [
        (FlightTicket, FlightTicketSerializer),
        (Hotel, HotelSerializer),
        (Activity, ActivitySerializer),
    ]


# Function to get model by item type


class ItemAPIView(APIView):
    pagination_class = CustomPagination
    parser_classes = [JSONParser]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAgentPermission]
        return [permission() for permission in permission_classes]

    def post(self, request, *args, **kwargs):
        action = kwargs.get('action')
        type_param = request.data.get('type')
        if not type_param:
            return Response({'result': False, 'errorMsg': 'Please put type'}, status=400)
        model, serializer_class = get_model_and_serializer(type_param)

        if action == 'insert':
            if 'image_alt' not in request.data:
                request.data['image_alt'] = request.data.get('name')
            serializer = serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(owner=request.user, image_src=request.data.get('image_src'))
                refresh_redis_packages_with_items()
                return Response(
                    {'result': True, 'message': 'Data saved successfully', 'data': serializer.data, 'errorMsg': ''},
                    status=status.HTTP_201_CREATED)
            return Response(
                {'result': False, 'errorMsg': 'Invalid data', 'message': "", 'data': None},
                status=status.HTTP_400_BAD_REQUEST)

        elif action == 'delete':
            obj_id = request.data.get('id')
            if not obj_id:
                return Response({'result': False, 'errorMsg': 'Please put id'}, status=400)
            model, _ = get_model_and_serializer(type_param)
            obj = model.objects.filter(id=obj_id).first()
            if obj:
                with transaction.atomic():
                    obj.soft_delete()  # soft delete
                    soft_delete_package_item(obj_id, type_param)
                    update_related_packages_price_by_item(obj)
                    delete_cart_item(obj_id, type_param)
                refresh_redis_packages_with_items()
                return Response({'result': True, 'message': 'Object soft-deleted successfully'}, status=204)
            else:
                return Response({'result': False, 'errorMsg': 'This id does not exist'}, status=404)

        elif action == 'update':
            obj_id = request.data.get('id')
            if not obj_id:
                return Response({'result': False, 'errorMsg': 'Please put id'}, status=400)
            model, serializer_class = get_model_and_serializer(type_param)

            obj = model.objects.filter(id=obj_id).first()
            if obj:
                serializer = serializer_class(obj, data=request.data, partial=True)
                if serializer.is_valid():
                    image_src = request.data.get('image_src')
                    if image_src:
                        serializer.save(owner=request.user, image_src=image_src)
                    else:
                        serializer.save(owner=request.user)
                    package_items = PackageItem.objects.filter(
                        Q(item_object_id=obj_id) & Q(type=type_param)
                    )
                    updated_detail = get_item_detail(type_param, obj)
                    update_related_packages_price_by_item(obj)
                    batch_size = 100
                    for i in range(0, len(package_items), batch_size):
                        with transaction.atomic():
                            batch = package_items[i:i + batch_size]
                            for package_item in batch:
                                package_item.detail = updated_detail
                            PackageItem.objects.bulk_update(batch, ['detail'])

                    refresh_redis_packages_with_items()
                    return Response(
                        {'result': True, 'message': 'Update successful', 'data': serializer.data, 'errorMsg': None})
                return Response(
                    {'result': False, 'message': 'Invalid data', 'data': None, 'errorMsg': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'result': False, 'message': 'This id does not exist', 'data': None, 'errorMsg': None},
                                status=status.HTTP_404_NOT_FOUND)

    def get(self, request, *args, **kwargs):
        type_param = request.query_params.get('type')
        obj_id = request.query_params.get('id')

        if not type_param or not obj_id:
            return Response(
                {'result': False, 'errorMsg': 'Both Type and ID parameters are required.', 'message': "",
                 'data': None}, status=status.HTTP_400_BAD_REQUEST)

        model, serializer_class = get_model_and_serializer(type_param)
        if not model or not serializer_class:
            return Response(
                {'result': False, 'errorMsg': 'Invalid Type parameter.', 'message': "",
                 'data': None}, status=status.HTTP_400_BAD_REQUEST)

        try:
            obj = model.objects.get(id=obj_id)
        except model.DoesNotExist:
            return Response(
                {'result': False, 'errorMsg': f'Object with ID {obj_id} does not exist for Type {type_param}.',
                 'message': "", 'data': None}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_class(obj, context={'request': request})
        return Response(
            {"result": True, "message": "Data fetched successfully", "data": serializer.data, "errorMsg": ""},
            status=status.HTTP_200_OK)


@api_view(["POST"])
def add_package(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        owner = request.user
        items_data = data.get('items', [])
        custom_package = insert_package(data, owner, items_data)
        serializer = CustomPackageSerializer(custom_package)
        return JsonResponse(
            {"result": True, "message": "Package added successfully", "data": serializer.data, "errorMsg": ""},
            status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"result": False, "message": "", "errorMsg": str(e), "data": None},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def update_package(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        package_id = data.get('id')
        # Ensure package_id is provided
        if not package_id:
            return JsonResponse({"result": False, "errorMsg": "Package ID is required", "message": "", "data": None},
                                status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            custom_package = CustomPackage.objects.select_for_update().get(id=package_id)

            custom_package.name = data.get('name', custom_package.name)
            custom_package.description = data.get('description', custom_package.description)
            custom_package.image_src = data.get('image_src', custom_package.image_src)
            # Process items_data if provided
            items_data = data.get('items', [])
            given_item_set = {(item['type'], item['id']) for item in items_data}

            existing_items = custom_package.packageitem_set.all()

            for item in existing_items:
                item_type = item.type
                item_id = item.item_object_id
                if (item_type, item_id) not in given_item_set:
                    item.soft_delete()

            # 遍历给定项目列表，更新或创建项目
            for item_data in items_data:
                item_id = item_data.get('id')
                item_type = item_data.get('type')
                number = item_data.get('number')

                model = get_model_by_item_type(item_type)
                model_instance = model.objects.get(id=item_id)

                # 更新或创建 PackageItem 对象
                package_item, created = PackageItem.objects.update_or_create(
                    package=custom_package,
                    item_content_type=ContentType.objects.get_for_model(model),
                    item_object_id=item_id,
                    defaults={'quantity': number, 'type': item_type}
                )

                # 更新项目的详细信息
                package_item.detail = get_item_detail(item_type, model_instance)
                package_item.save()

            custom_package.save()
            serializer = CustomPackageSerializer(custom_package)
            refresh_redis_packages_with_items()
            return JsonResponse(
                {"result": True, "message": "Package updated successfully", "errorMsg": "", "data": serializer.data},
                status=status.HTTP_200_OK)
    except CustomPackage.DoesNotExist:
        return JsonResponse({"result": False, "errorMsg": "Package not found", "message": "", "data": None},
                            status=status.HTTP_400_BAD_REQUEST)
    except ObjectDoesNotExist:
        return JsonResponse({"result": False, "errorMsg": "One or more items not found", "message": "", "data": None},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JsonResponse({"result": False, "errorMsg": str(e), "message": "", "data": None},
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def view_packages(request):
    pagination_class = CustomPagination()
    id = request.query_params.get('id')
    if id:
        try:
            custom_package = CustomPackage.objects.get(id=id)
            serializer = CustomPackageSerializer(custom_package)
            return Response({"result": True, "message": "Package found", "data": serializer.data, "errorMsg": ""},
                            status=status.HTTP_200_OK)
        except CustomPackage.DoesNotExist:
            return Response({"result": False, "message": "", "errorMsg": "Package not found", "data": None},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        queryset = CustomPackage.objects.all()
        page = pagination_class.paginate_queryset(queryset, request)
        serializer = CustomPackageSerializer(page, many=True)
        return pagination_class.get_paginated_response(
            {"result": True, "message": "Packages list", "data": serializer.data, "errorMsg": ""})


@api_view(['GET'])
def view_user_packages(request):
    pagination_class = CustomPagination()
    owner = request.user
    queryset = CustomPackage.objects.prefetch_related('packageitem_set').filter(owner=owner)
    page = pagination_class.paginate_queryset(queryset, request)
    serializer = CustomPackageSerializer(queryset, many=True)
    return Response(
        {"result": True, "message": "User packages list", "data": serializer.data, "errorMsg": ""})


@api_view(['GET'])
@permission_classes([AllowAny])
def packages_with_items(request):
    response_data = get_packages_with_items(None)
    return JsonResponse(
        {"result": True, "message": "select all packages and items successfully", "data": response_data,
         "errorMsg": ""},
        status=status.HTTP_200_OK)


@api_view(['GET'])
def view_agent_products(request):
    response_data = get_packages_with_items(request.user)
    return JsonResponse(
        {"result": True, "message": "select the agent packages and items successfully", "data": response_data},
        status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def trend_package(request):
    trend_packages_by_user_order = UserOrder.objects.filter(is_delete=False, is_agent_package=1, name__gt='') \
                                       .exclude(status=9).exclude(name=user_create_package_name).values(
        'package_id').annotate(
        package_count=Count('package_id')).order_by('-package_count')[:3]
    trend_packages_ids = [package['package_id'] for package in trend_packages_by_user_order]
    if len(trend_packages_ids) < 3:
        trend_packages_details = CustomPackage.objects.filter(is_delete=0)[:3]
    else:
        trend_packages_details = CustomPackage.objects.filter(id__in=trend_packages_ids)
    return JsonResponse(
        {"result": True, "message": "select trend packages successfully",
         "data": CustomPackageSerializer(trend_packages_details, many=True).data},
        status=status.HTTP_200_OK)


@api_view(['POST'])
def delete_package(request):
    obj_id = request.data.get('id')
    if not obj_id:
        return Response({'result': False, 'errorMsg': 'Please put id', 'message': "", 'data': None},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        obj = CustomPackage.objects.get(id=obj_id)
        obj.soft_delete()  # Assuming soft_delete() marks the is_delete field
        refresh_redis_packages_with_items()
        return Response({'result': True, 'message': 'Package deleted successfully', 'data': None, 'errorMsg': ""},
                        status=status.HTTP_200_OK)
    except CustomPackage.DoesNotExist:
        return Response({'result': False, 'errorMsg': 'Package not found', 'message': "", 'data': None},
                        status=status.HTTP_400_BAD_REQUEST)


def insert_package(data, owner, items_data):
    with transaction.atomic():
        input_price = data.get('price', 0)  # Get input price

        if input_price != 0:  # If input price is not 0, use it directly
            total_price = input_price
        else:
            total_price = sum(item_data.get('number') * get_model_by_item_type(item_data.get('type')).objects.get(
                id=item_data.get('id')).price for item_data in items_data)
        image_alt = data.get('image_alt')
        if not image_alt:
            image_alt = data.get('name')
        custom_package = CustomPackage.objects.create(
            name=data.get('name', ' '),
            description=data.get('description', ' '),
            owner=owner,
            price=total_price,
            image_src=data.get('image_src'),
            image_alt=image_alt,
            is_user=not owner.is_agent,
            features=data.get('features', [])
        )

        for item_data in items_data:
            item_type = item_data.get('type')
            item_id = item_data.get('id')
            quantity = item_data.get('number')

            model = get_model_by_item_type(item_type)
            model_instance = model.objects.get(id=item_id)

            PackageItem.objects.create(
                package=custom_package,
                item_content_type=ContentType.objects.get_for_model(model),
                item_object_id=item_id,
                quantity=quantity,
                type=item_type,
                detail=get_item_detail(item_type, model_instance)
            )

        refresh_redis_packages_with_items()
        return custom_package
