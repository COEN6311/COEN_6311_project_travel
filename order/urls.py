from . import views

from django.urls import path

urlpatterns = [
    path('place', views.place_order, name='place_order'),
    path('payment', views.payment_order, name='payment_order'),
]
