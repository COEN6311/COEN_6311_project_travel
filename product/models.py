from django.db import models

from django.db import models
from db.base_model import BaseModel
from user.models import User


class Item(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    owner = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)

    class Meta:
        abstract = True


class FlightTicket(Item):
    flight_number = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    # arrival_time = models.DateTimeField()
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)

class Hotel(Item):
    location = models.CharField(max_length=255)
    check_in = models.DateField()
    check_out = models.DateField()
    room_type = models.CharField(max_length=100)