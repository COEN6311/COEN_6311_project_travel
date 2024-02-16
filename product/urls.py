from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from django.urls import path
from .views import CustomAPIView

urlpatterns = [
    path('item/<str:action>', CustomAPIView.as_view(), name='custom_api'),
    path('item/', CustomAPIView.as_view(), name='custom_api'),
    path('package/insert/', views.add_package, name='add_package'),
]
