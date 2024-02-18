import json
from itertools import chain

from django.db import transaction
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from user.customPermission import IsAgentPermission
from .serializers import FlightTicketSerializer, HotelSerializer, CustomPackageSerializer, ActivitySerializer
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from .models import CustomPackage, PackageItem, FlightTicket, Hotel, User, Activity


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


# Function to get all models and their serializers
def get_all_models_and_serializers():
    return [
        (FlightTicket, FlightTicketSerializer),
        (Hotel, HotelSerializer),
    ]


# Function to get model by item type
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


class CustomAPIView(APIView):
    pagination_class = CustomPagination

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
            serializer = serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(owner=request.user)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)

        elif action == 'delete':
            obj_id = request.data.get('id')
            if not obj_id:
                return Response({'result': False, 'errorMsg': 'Please put id'}, status=400)
            model, _ = get_model_and_serializer(type_param)
            obj = model.objects.filter(id=obj_id).first()
            if obj:
                obj.delete()
                return Response(status=204)
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
                    serializer.save(owner=request.user)
                    return Response(serializer.data)
                return Response(serializer.errors, status=400)
            else:
                return Response({'result': False, 'errorMsg': 'This id does not exist'}, status=404)

    def get(self, request, *args, **kwargs):
        type_param = request.query_params.get('type')
        obj_id = request.query_params.get('id')
        all_data = None
        if obj_id and not type_param:
            return Response({'error': 'When an ID is provided, the Type parameter is required.'}, status=400)
        all_models_and_serializers = get_all_models_and_serializers()
        if type_param:
            model, serializer_class = get_model_and_serializer(type_param)
            if model and serializer_class:
                queryset = model.objects.all().order_by('-create_time')
                if obj_id:
                    queryset = queryset.filter(id=obj_id)
                all_data = [(queryset, serializer_class)]
        else:
            all_data = [(model.objects.all().order_by('-create_time'), serializer) for model, serializer in
                        all_models_and_serializers]

        combined_queryset = list(chain.from_iterable([data[0] for data in all_data]))

        # Page handling
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(combined_queryset, request, view=self)
        if page is not None:
            serialized_data = []
            for obj in page:
                for model, serializer_class in all_models_and_serializers:
                    if isinstance(obj, model):
                        serializer = serializer_class(obj)
                        serialized_data.append(serializer.data)
                        break
            return paginator.get_paginated_response(serialized_data)


# Function to add a package
def add_package(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name')
        description = data.get('description')
        owner = request.user  # Use the authenticated user as the owner
        items_data = data.get('items', [])
        price_provided = 'price' in data

        total_price = data.get('price', 0) if price_provided else 0

        with transaction.atomic():  # Start a transaction
            # Create CustomPackage object within the transaction
            custom_package = CustomPackage.objects.create(
                name=name,
                description=description,
                owner=owner,
                price=total_price
            )

            for item in items_data:
                item_type = item.get('type')
                item_id = item.get('id')
                number = item.get('number')

                model = get_model_by_item_type(item_type)
                try:
                    # Attempt to get the instance directly, avoiding redundant checks
                    model_instance = model.objects.get(id=item_id)
                    if not price_provided:
                        # Calculate the total price
                        total_price += model_instance.price * number
                except model.DoesNotExist:
                    # If the instance doesn't exist, raise a more specific exception
                    raise ObjectDoesNotExist(f"{model.__name__} with ID {item_id} not found.")
                # Get the ContentType for the model
                item_content_type = ContentType.objects.get_for_model(model)
                PackageItem.objects.create(
                    package=custom_package,
                    item_content_type=item_content_type,
                    item_object_id=item_id,
                    quantity=number,
                    type=item_type  # Use this field according to your business logic
                )

            if not price_provided:
                # 更新CustomPackage的价格
                custom_package.price = total_price
                custom_package.save()
            serializer = CustomPackageSerializer(custom_package)
            return JsonResponse({"status": "success", "package": serializer.data})

    except ObjectDoesNotExist as e:
        # If an item does not exist during validation, return an error response
        return JsonResponse({"status": "error", "message": str(e)})
    except ValueError as e:
        # If an invalid type is provided, return an error response
        return JsonResponse({"status": "error", "message": str(e)})
    except Exception as e:
        # Catch all other exceptions
        return JsonResponse({"status": "error", "message": "Unexpected error occurred."})


@require_http_methods(["POST"])
def update_package(request, package_id):
    pagination_class = CustomPagination
    try:
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name')
        description = data.get('description')
        price = data.get('price')
        items_data = data.get('items', [])  # 包含项目更新信息

        with transaction.atomic():  # 使用事务确保数据一致性
            # 尝试获取套餐
            custom_package = CustomPackage.objects.select_for_update().get(id=package_id)

            # 更新基本字段（如果提供）
            if name:
                custom_package.name = name
            if description:
                custom_package.description = description
            if price:
                custom_package.price = price

            # 处理项目依赖关系的更新
            existing_item_ids = [item['id'] for item in items_data if 'id' in item]
            # 删除不存在于更新数据中的项目
            custom_package.packageitem_set.exclude(item_object_id__in=existing_item_ids).delete()

            for item in items_data:
                item_id = item.get('id')
                item_type = item.get('type')
                number = item.get('number')

                # 根据item_type获取对应的model
                model = get_model_by_item_type(item_type)

                # 检查item是否存在
                model_instance = model.objects.get(id=item_id)

                # 获取或创建PackageItem
                package_item, created = PackageItem.objects.get_or_create(
                    package=custom_package,
                    item_content_type=ContentType.objects.get_for_model(model),
                    item_object_id=item_id,
                    defaults={'quantity': number, 'type': item_type}
                )
                if not created:
                    # 如果项目已存在，则更新数量
                    package_item.quantity = number
                    package_item.save()

            custom_package.save()  # 保存套餐更新

            return JsonResponse({"status": "success", "message": "Package updated successfully."})
    except CustomPackage.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Package not found."})
    except ObjectDoesNotExist:
        return JsonResponse({"status": "error", "message": "One or more items not found."})
    except Exception as e:
        # 捕获并返回其他所有异常
        return JsonResponse({"status": "error", "message": str(e)})



@api_view(['GET'])
def view_packages(request, package_id=None):
    pagination_class = CustomPagination()
    if package_id:
        try:
            custom_package = CustomPackage.objects.get(id=package_id)
            serializer = CustomPackageSerializer(custom_package)
            return Response({"status": "success", "package": serializer.data})
        except CustomPackage.DoesNotExist:
            return Response({"status": "error", "message": "Package not found."})
    else:
        queryset = CustomPackage.objects.all()
        page = pagination_class.paginate_queryset(queryset, request)
        serializer = CustomPackageSerializer(page, many=True, context={'request': request})
        return pagination_class.get_paginated_response(serializer.data)


@api_view(['GET'])
def view_user_packages(request):
    try:
        owner = request.user
    except User.DoesNotExist:
        return Response({"status": "error", "message": "User not found."})

    # 获取该用户创建的所有CustomPackage
    queryset = CustomPackage.objects.filter(owner=owner)

    # 使用自定义分页
    paginator = CustomPagination()
    page = paginator.paginate_queryset(queryset, request)

    # 序列化分页的套餐
    serializer = CustomPackageSerializer(page, many=True, context={'request': request})

    return paginator.get_paginated_response(serializer.data)