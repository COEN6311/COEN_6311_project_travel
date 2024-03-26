
from django.urls import path

from remark import views

urlpatterns = [
    path('addremark', views.add_remark, name='add_remark')

]
