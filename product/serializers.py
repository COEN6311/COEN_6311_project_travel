from rest_framework import serializers
from .models import FlightTicket, Hotel, PackageItem, CustomPackage, Activity

SERIALIZER_TYPE_MAP = {
    'FlightTicketSerializer': 1,
    'HotelSerializer': 2,
    'ActivitySerializer': 3,
}


class SerializerTypeMixin:
    def get_type(self, obj):
        serializer_name = self.__class__.__name__
        return SERIALIZER_TYPE_MAP.get(serializer_name, 0)


class FlightTicketSerializer(SerializerTypeMixin, serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = FlightTicket
        fields = '__all__'


class HotelSerializer(SerializerTypeMixin, serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = '__all__'


class ActivitySerializer(SerializerTypeMixin, serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = '__all__'


class PackageItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageItem
        fields = ['id', 'type', 'quantity']


class CustomPackageSerializer(serializers.ModelSerializer):
    items = PackageItemSerializer(source='packageitem_set', many=True)

    class Meta:
        model = CustomPackage
        fields = ['id', 'name', 'description', 'owner', 'price', 'items']
