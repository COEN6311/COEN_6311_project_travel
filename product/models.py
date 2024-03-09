from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from db.base_model import BaseModel
from user.models import User
from django.db import models

from utils.times import default_start_date, default_end_date


class Item(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    start_date = models.DateField(default=default_start_date, blank=True, null=True)
    end_date = models.DateField(default=default_end_date, blank=True, null=True)
    image_src = models.URLField(max_length=1024, blank=True, null=True)
    image_alt = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True


class FlightTicket(Item):
    flight_number = models.CharField(max_length=100)
    seat_class = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.TimeField(verbose_name='departure_time', blank=True, null=True)
    arrival_time = models.TimeField(verbose_name='arrival_time', blank=True, null=True)


class Hotel(Item):
    hotel_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    room = models.CharField(max_length=255, blank=True, null=True)
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)


class Activity(Item):
    event = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    time = models.TimeField(verbose_name='time', blank=True, null=True)


class CustomPackage(Item):
    features = models.JSONField(default=list)
    is_user = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-create_time']


class PackageItem(BaseModel):
    package = models.ForeignKey(CustomPackage, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    item_object_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_content_type', 'item_object_id')
    type = models.PositiveSmallIntegerField()
    detail = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = ('package', 'item_content_type', 'item_object_id', 'type', 'is_delete')


def soft_delete_package_item(item_id, item_type):
    package_items = PackageItem.objects.filter(
        item_object_id=item_id,
        type=item_type
    )
    package_items.update(is_delete=True)
