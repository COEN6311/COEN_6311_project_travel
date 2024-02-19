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
    image_url = models.URLField(max_length=1024, blank=True, null=True)
    start_date = models.DateField(default=default_start_date, blank=True, null=True)
    end_date = models.DateField(default=default_end_date, blank=True, null=True)

    # todo handle order system's date
    # todo feature

    class Meta:
        abstract = True


class FlightTicket(Item):
    flight_number = models.CharField(max_length=100)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.TimeField(verbose_name='departure_time', blank=True, null=True)


class Hotel(Item):
    location = models.CharField(max_length=255)
    # room_type = models.CharField(max_length=100)


class Activity(Item):
    location = models.CharField(max_length=255)


class CustomPackage(Item):
    name = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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

    type = models.PositiveSmallIntegerField()  # 考虑是否还需要这个字段与GenericForeignKey一起使用。

    class Meta:
        unique_together = ('package', 'item_content_type', 'item_object_id', 'type')
