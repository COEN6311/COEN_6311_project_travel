import json
import time

from django.core.cache import cache
from rest_framework import serializers

from order.constant import OrderStatus
from order.models import UserOrder, AgentOrder
from user.models import User
from utils.number_util import calculate_price_taxed


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']


class UserOrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    price = serializers.FloatField()  # or serializers.FloatField()
    amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserOrder
        fields = ['id', 'order_number', 'status', 'price', 'amount', 'name', 'description', 'created_date', 'user']

    def get_status(self, obj):
        status_code = obj.status
        return OrderStatus.get_description(status_code)

    def get_amount(self, obj):
        return float(calculate_price_taxed(obj.price))


class AgentOrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    price = serializers.FloatField()  # or serializers.FloatField()
    amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AgentOrder
        fields = ['id', 'order_number', 'agent_order_number', 'status', 'price', 'amount', 'name', 'description',
                  'created_date', 'user']

    def get_status(self, obj):
        status_code = obj.status
        return OrderStatus.get_description(status_code)

    def get_amount(self, obj):
        return float(calculate_price_taxed(obj.price))
