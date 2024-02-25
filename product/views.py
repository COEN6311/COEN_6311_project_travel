import json
import time
from itertools import chain

from django.db import transaction
from django.views.decorators.http import require_http_methods
from line_profiler import profile
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import JSONParser
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
from django.core.cache import cache


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
            serializer = serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(owner=request.user, image_src=request.data.get('image_src'))
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
                obj.soft_delete()  # soft delete
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
                    serializer.save(owner=request.user)
                    return Response(serializer.data)
                return Response(serializer.errors, status=400)
            else:
                return Response({'result': False, 'errorMsg': 'This id does not exist'}, status=404)

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

        with transaction.atomic():
            custom_package = CustomPackage.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                owner=owner,
                price=data.get('price', 0),
                image_src=data.get('image_src'),
                features=data.get('features')
            )

            for item in items_data:
                item_type = item.get('type')
                item_id = item.get('id')
                quantity = item.get('number')

                model = get_model_by_item_type(item_type)
                model_instance = model.objects.get(id=item_id)
                PackageItem.objects.create(
                    package=custom_package,
                    item_content_type=ContentType.objects.get_for_model(model),
                    item_object_id=item_id,
                    quantity=quantity,
                    type=item_type
                )

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
            custom_package.price = data.get('price', custom_package.price)

            # Process items_data if provided
            items_data = data.get('items', [])
            existing_item_ids = [item.get('id') for item in items_data if item.get('id')]
            custom_package.packageitem_set.exclude(item_object_id__in=existing_item_ids).delete()

            for item in items_data:
                item_id = item.get('id')
                item_type = item.get('type')
                number = item.get('number')

                model = get_model_by_item_type(item_type)
                model_instance = model.objects.get(id=item_id)

                package_item, created = PackageItem.objects.update_or_create(
                    package=custom_package,
                    item_content_type=ContentType.objects.get_for_model(model),
                    item_object_id=item_id,
                    defaults={'quantity': number, 'type': item_type}
                )

            custom_package.save()
            serializer = CustomPackageSerializer(custom_package)
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
    queryset = CustomPackage.objects.filter(owner=owner)
    page = pagination_class.paginate_queryset(queryset, request)
    serializer = CustomPackageSerializer(page, many=True)
    return pagination_class.get_paginated_response(
        {"result": True, "message": "User packages list", "data": serializer.data, "errorMsg": ""})


@api_view(['POST'])
def delete_package(request):
    obj_id = request.data.get('id')
    if not obj_id:
        return Response({'result': False, 'errorMsg': 'Please put id', 'message': "", 'data': None},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        obj = CustomPackage.objects.get(id=obj_id)
        obj.soft_delete()  # Assuming soft_delete() marks the is_delete field
        return Response({'result': True, 'message': 'Package deleted successfully', 'data': None, 'errorMsg': ""},
                        status=status.HTTP_200_OK)
    except CustomPackage.DoesNotExist:
        return Response({'result': False, 'errorMsg': 'Package not found', 'message': "", 'data': None},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def packages_with_items(request):
    start_time = time.time()

    # Retrieve all packages
    packages = CustomPackage.objects.all()
    package_serializer = CustomPackageSerializer(packages, many=True)

    print(f"Retrieving and serializing packages took {time.time() - start_time} seconds")
    start_time = time.time()

    # Retrieve all items
    flight_tickets = FlightTicket.objects.all()
    hotels = Hotel.objects.all()
    activities = Activity.objects.all()

    print(f"Retrieving all items took {time.time() - start_time} seconds")
    start_time = time.time()

    # Serialize all items
    flight_ticket_serializer = FlightTicketSerializer(flight_tickets, many=True)
    hotel_serializer = HotelSerializer(hotels, many=True)
    activity_serializer = ActivitySerializer(activities, many=True)
    cache.set('flight_tickets', flight_tickets)
    cache.set('hotels', hotels)
    cache.set('activities', activities)
    print(f"Serializing all items took {time.time() - start_time} seconds")
    start_time = time.time()

    # Prepare response data
    response_data = []

    # Append packages to response data with their details
    for package_data in package_serializer.data:
        response_data.append(package_data)
    print(f"Building response data took {time.time() - start_time} seconds")

    # Append items to response data
    for item_data in flight_ticket_serializer.data:
        response_data.append(item_data)
    print(f"Building response data took {time.time() - start_time} seconds")

    for item_data in hotel_serializer.data:
        response_data.append(item_data)
    print(f"Building response data took {time.time() - start_time} seconds")

    for item_data in activity_serializer.data:
        response_data.append(item_data)

    print(f"Building response data took {time.time() - start_time} seconds")

    return Response(response_data)
