from . import views, task

from django.urls import path

urlpatterns = [
    path('place', views.place_order, name='place_order'),
    path('views', views.view_orders, name='view_orders'),
    path('payment', views.payment_order, name='payment_order'),
    path('cancel', views.cancel_order, name='cancel_order'),
    path('agent/report', views.agent_report, name='agent_report'),
]
