from . import views

from django.urls import path

urlpatterns = [
    path('place', views.place_order, name='place_order'),
]
