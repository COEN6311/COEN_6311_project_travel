from . import views

from django.urls import path

urlpatterns = [
    path('addItem', views.add_item, name='addItem'),
    path('query', views.query_by_user, name='query'),
    path('deleteItem', views.delete_item, name='deleteItem'),
    path('cartCheckout', views.cartCheckout, name='cartCheckout'),
    path('packageCheckout', views.packageCheckout, name='packageCheckout'),
]
