from rest_framework import serializers
from .models import FlightTicket, Hotel


class FlightTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightTicket
        fields = '__all__'


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = '__all__'
