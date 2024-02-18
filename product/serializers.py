from rest_framework import serializers
from .models import FlightTicket, Hotel, PackageItem, CustomPackage, Activity


class FlightTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightTicket
        fields = '__all__'


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
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
