from rest_framework import serializers
from .models import FlightTicket, Hotel, PackageItem, CustomPackage, Activity, Item

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

    def get_imageSrc(self, obj):
        return obj.image_src

    def get_imageAlt(self, obj):
        return obj.name


class FlightTicketSerializer(ItemSerializer):
    details = serializers.SerializerMethodField(read_only=True)
    options = serializers.CharField(default='Included: Flight', read_only=True)
    type = serializers.CharField(default='flight', read_only=True)
    flight_number = serializers.CharField(write_only=True)
    arrival_time = serializers.TimeField(write_only=True)
    departure_time = serializers.TimeField(write_only=True)
    seat_class = serializers.CharField(write_only=True)
    destination = serializers.CharField(write_only=True)

    class Meta:
        model = FlightTicket
        fields = ['id', 'name', 'price', 'description', 'options', 'imageSrc', 'imageAlt', 'type', 'details',
                  'flight_number', 'arrival_time', 'departure_time', 'seat_class', 'destination']

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

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'price', 'description', 'options', 'imageSrc', 'imageAlt', 'type', 'details',
                  'hotel_name', 'address', 'room', 'check_in_time', 'check_out_time']

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

    class Meta:
        model = Activity
        fields = ['id', 'name', 'price', 'description', 'options', 'imageSrc', 'imageAlt', 'type', 'details', 'event',
                  'location', 'address', 'time']

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
    items = PackageItemSerializer(source='packageitem_set', many=True)

    class Meta:
        model = CustomPackage
        fields = ['id', 'name', 'description', 'owner', 'price', 'items']
