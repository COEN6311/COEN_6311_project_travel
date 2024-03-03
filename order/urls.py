from . import views, task

from django.urls import path

urlpatterns = [
    path('place', views.place_order, name='place_order'),
    path('views', views.view_orders, name='view_orders'),
    path('payment', views.payment_order, name='payment_order'),
    path('test', task.change_order_status_task, name='change_order_status_task'),
]
