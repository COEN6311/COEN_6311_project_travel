from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from django.urls import path
from .views import ItemAPIView, view_user_packages

urlpatterns = [
    path('item/<str:action>', ItemAPIView.as_view(), name='custom_api'),
    path('item', ItemAPIView.as_view(), name='view_custom_api'),
    path('package/insert', views.add_package, name='add_package'),
    path('package/user', view_user_packages, name='view_user_packages'),
    path('package/', views.view_packages, name='view_packages'),
    path('package/delete', views.delete_package, name='delete_package'),
    path('package/update', views.update_package, name='update_package'),
]
