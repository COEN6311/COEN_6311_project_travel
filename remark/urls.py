
from django.urls import path

from remark import views

urlpatterns = [
    path('add', views.add_remark, name='add_remark')

]
