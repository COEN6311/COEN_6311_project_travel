import json
import time

from django.core.cache import cache
from rest_framework import serializers

from order.constant import OrderStatus
from order.models import UserOrder, AgentOrder
from user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']


class UserOrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserOrder
        fields = ['id', 'order_number', 'status', 'price', 'name', 'description', 'created_date', 'user']

    def get_status(self, obj):
        status_code = obj.status
        return OrderStatus.get_description(status_code)


class AgentOrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AgentOrder
        fields = ['id', 'order_number', 'agent_order_number', 'status', 'price', 'name', 'description', 'created_date',
                  'user']

    def get_status(self, obj):
        status_code = obj.status
        return OrderStatus.get_description(status_code)
