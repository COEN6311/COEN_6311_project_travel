import json
import time

from django.core.cache import cache
from rest_framework import serializers
from .models import FlightTicket, Hotel, PackageItem, CustomPackage, Activity, Item
from .utils import detail_cache

SERIALIZER_TYPE_MAP = {
    'FlightTicketSerializer': 1,
    'HotelSerializer': 2,
    'ActivitySerializer': 3,
}


class SerializerTypeMixin:
    def get_type(self, obj):
        serializer_name = self.__class__.__name__
        return SERIALIZER_TYPE_MAP.get(serializer_name, 0)


class ItemSerializer(serializers.ModelSerializer):
    imageSrc = serializers.SerializerMethodField()
    imageAlt = serializers.SerializerMethodField()
    createAt = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField()

    def get_rating(self, obj):
        rating_decimal = obj.rating  # 假设 rating 是 Decimal 字段
        rating_float = float(rating_decimal)
        return rating_float

    def get_imageSrc(self, obj):
        return obj.image_src

    def get_imageAlt(self, obj):
        if hasattr(obj, 'image_alt'):
            return obj.image_alt
        else:
            return obj.name

    def get_createAt(self, obj):
        return obj.create_time.date().strftime("%Y-%m-%d")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        rating = data.get('rating')
        rating_count = data.get('rating_count')
        if rating is not None and rating == '0.0':
            del data['rating']

        if rating_count is not None and rating_count == 0:
            del data['rating_count']
        return data


class FlightTicketSerializer(ItemSerializer):
    details = serializers.SerializerMethodField(read_only=True)
    options = serializers.CharField(default='Included: Flight', read_only=True)
    type = serializers.CharField(default='flight', read_only=True)
    flight_number = serializers.CharField(write_only=True)
    arrival_time = serializers.TimeField(write_only=True)
    departure_time = serializers.TimeField(write_only=True)
    seat_class = serializers.CharField(write_only=True)
    destination = serializers.CharField(write_only=True)
    price = serializers.FloatField()  # or serializers.FloatField()
    image_alt = serializers.CharField(write_only=True)

    class Meta:
        model = FlightTicket
        fields = ['id', 'name', 'price', 'description', 'options', 'imageSrc', 'imageAlt', 'type', 'details',
                  'image_alt', 'flight_number', 'arrival_time', 'departure_time', 'seat_class', 'destination', 'rating',
                  'rating_count', 'start_date', 'end_date', 'createAt']

    def get_details(self, obj):
        return [
            {
                'name': 'Flight Details',
                'items': [
                    f'Destination: {obj.destination}',
                    f'Flight number: {obj.flight_number}',
                    f'Class: {obj.seat_class}',
                    f'Departure: {obj.departure_time}',
                    f'Arrival: {obj.arrival_time}',
                ],
                'type': 'flight',
            }
        ]


class HotelSerializer(ItemSerializer):
    details = serializers.SerializerMethodField()
    options = serializers.CharField(default='Included: Hotel', read_only=True)
    type = serializers.CharField(default='hotel', read_only=True)

    hotel_name = serializers.CharField(write_only=True)
    address = serializers.CharField(write_only=True)
    room = serializers.CharField(write_only=True)
    check_in_time = serializers.TimeField(write_only=True)
    check_out_time = serializers.TimeField(write_only=True)
    price = serializers.FloatField()  # or serializers.FloatField()
    image_alt = serializers.CharField(write_only=True)

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'price', 'description', 'options', 'imageSrc', 'imageAlt', 'type', 'details',
                  'image_alt', 'hotel_name', 'address', 'room', 'check_in_time', 'check_out_time', 'start_date',
                  'rating', 'rating_count', 'end_date', 'createAt']

    def get_details(self, obj):
        return [
            {
                'name': 'Hotel Details',
                'items': [
                    f'Hotel name: {obj.hotel_name}',
                    f'Room: {obj.room}',
                    f'Address: {obj.address}',
                    f'Check-in: {obj.check_in_time.strftime("%H:%M") if obj.check_in_time else "N/A"}',
                    f'Check-out: {obj.check_out_time.strftime("%H:%M") if obj.check_out_time else "N/A"}',
                ],
                'type': 'hotel',
            }
        ]


class ActivitySerializer(ItemSerializer):
    details = serializers.SerializerMethodField(read_only=True)
    options = serializers.CharField(default='Included: Activities', read_only=True)
    type = serializers.CharField(default='activity', read_only=True)
    event = serializers.CharField(write_only=True)
    location = serializers.CharField(write_only=True)
    address = serializers.CharField(write_only=True)
    time = serializers.TimeField(write_only=True)
    price = serializers.FloatField()  # or serializers.FloatField()
    image_alt = serializers.CharField(write_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'name', 'price', 'description', 'options', 'imageSrc', 'imageAlt', 'type', 'details', 'event',
                  'image_alt', 'location', 'address', 'time', 'rating', 'rating_count',
                  'start_date', 'end_date', 'createAt']

    def get_details(self, obj):
        return [
            {
                'name': obj.name,
                'items': [
                    f'Event: {obj.event}',
                    f'Location: {obj.location}',
                    f'Address: {obj.address}',
                    f'Time: {obj.time.strftime("%H:%M") if obj.time else None}',
                ],
                'type': 'activity',
            }
        ]


class PackageItemSerializer(serializers.ModelSerializer):
    item_id = serializers.SerializerMethodField()

    class Meta:
        model = PackageItem
        fields = ['type', 'quantity', 'item_id']

    def get_item_id(self, obj):
        return obj.item_object_id


class CustomPackageSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField(read_only=True)
    options = serializers.SerializerMethodField(read_only=True)
    imageSrc = serializers.URLField(source='image_src', read_only=True)
    imageAlt = serializers.CharField(source='image_alt', read_only=True)
    type = serializers.CharField(default='package', read_only=True)
    features = serializers.JSONField(write_only=True)
    price = serializers.FloatField()  # or serializers.FloatField()
    image_alt = serializers.CharField(write_only=True)
    createAt = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomPackage
        fields = ['id', 'name', 'description', 'price', 'details', 'options', 'imageSrc', 'imageAlt', 'image_alt',
                  'type', 'features', 'createAt']

    def get_options(self, obj):
        options = []

        # Check if flight, hotel, or activity is included in the package
        package_items = obj.packageitem_set.all()
        for item in package_items:
            item_type = item.item_content_type.model_class().__name__
            if item_type == 'FlightTicket':
                options.append('Flights')
            elif item_type == 'Hotel':
                options.append('Hotel')
            elif item_type == 'Activity':
                options.append('Activities')

        # Include the options in the desired format
        options_str = ', '.join(options)
        return f"Included: {options_str}"

    def get_details(self, obj):
        # Get package features
        features = {
            'name': 'Features',
            'items': obj.features,
            'type': 'package',
        }

        details = [features]

        # Get details from package items
        for item in obj.packageitem_set.all():
            detail_data = item.detail
            if detail_data:
                detail_data['id'] = item.item_object_id
                details.append(detail_data)
        return details

    def get_createAt(self, obj):
        return obj.create_time.date().strftime("%Y-%m-%d")
