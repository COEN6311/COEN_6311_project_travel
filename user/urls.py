from django.urls import path
from user import views

urlpatterns = [
    path('register/', views.register_handle, name='user_register'), # handle user registers
    path('login/', views.user_login, name='user_login'), # user login
    path('logout/', views.user_logout, name='user_logout'), # user logout
    path('deactive/', views.deactivate_account, name='user_deactivate_account'),
    path('profile_update/', views.update_profile, name='user_profile_update'),
    path('confirm/', views.confirm_registration, name='confirm_registration')

]