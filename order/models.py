from django.db import models

from db.base_model import BaseModel
from user.models import User


class Order(BaseModel):
    status = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=255)
    description = models.TextField()
    order_details = models.JSONField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True)
    departure_date = models.DateField()
    payment_time = models.DateTimeField(blank=True, null=True)
    end_date = models.DateField()
    created_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        abstract = True


class UserOrder(Order):
    order_number = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_orders')


class AgentOrder(Order):
    agent_order_number = models.CharField(max_length=100)
    order_number = models.CharField(max_length=100)
    user_order = models.ForeignKey(UserOrder, related_name='agent_orders', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_user_orders')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_orders')


class Payment(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments_orders')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_users')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_time = models.DateTimeField(blank=True, null=True)
