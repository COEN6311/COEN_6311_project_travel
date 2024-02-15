from django.shortcuts import render

from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .models import FlightTicket, Hotel
from .serializers import FlightTicketSerializer, HotelSerializer
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomAPIView(APIView, PageNumberPagination):

    def post(self, request, *args, **kwargs):
        action = kwargs.get('action')
        type_param = request.data.get('type')
        if not type_param:
            return Response({'result': False, 'errorMsg': 'please put type'}, status=400)
        model, serializer_class = self.get_model_and_serializer(type_param)

        if action == 'insert':
            serializer = serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)

        elif action == 'delete':
            type_param = request.data.get('type')
            obj_id = request.data.get('id')
            if not obj_id:
                return Response({'result': False, 'errorMsg': 'please put id'}, status=400)
            if not type_param:
                return Response({'result': False, 'errorMsg': 'please put type'}, status=400)
            model, serializer_class = self.get_model_and_serializer(type_param)
            obj = model.objects.filter(id=obj_id).first()
            if obj:
                obj.delete()
                return Response(status=204)
            else:
                return Response({'result': False, 'errorMsg': 'this id does not exist'}, status=404)

        elif action == 'update':
            type_param = request.data.get('type')
            obj_id = request.data.get('id')
            if not obj_id:
                return Response({'result': False, 'errorMsg': 'please put id'}, status=400)
            if not type_param:
                return Response({'result': False, 'errorMsg': 'please put type'}, status=400)
            model, serializer_class = self.get_model_and_serializer(type_param)

            obj = model.objects.filter(id=obj_id).first()
            if obj:
                serializer = serializer_class(obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=400)
            else:
                return Response({'result': False, 'errorMsg': 'this id does not exist'}, status=404)


    def get(self, request, *args, **kwargs):
        type_param = request.query_params.get('type')
        obj_id = request.query_params.get('id')

        if obj_id and not type_param:
            return Response({'error': 'Type parameter is required when ID is provided.'}, status=400)

        model, serializer_class = self.get_model_and_serializer(type_param)

        if model and serializer_class:
            queryset = model.objects.all().order_by('-create_time')
            if obj_id:
                queryset = queryset.filter(id=obj_id)
        else:
            return Response({'error': 'Invalid or missing type parameter.'}, status=400)

        # 当指定了id时，不进行分页，直接返回结果
        if obj_id:
            serializer = serializer_class(queryset, many=True)
            return Response(serializer.data)

        # 分页处理
        page = self.pagination_class.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = serializer_class(page, many=True)
            return self.pagination_class.get_paginated_response(serializer.data)

        # 如果不需要分页（理论上不会执行到这里，因为分页已经处理）
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)

    def get_model_and_serializer(self, type_param):
        if type_param == '1':
            return FlightTicket, FlightTicketSerializer
        elif type_param == '2':
            return Hotel, HotelSerializer
        else:
            return None, None

