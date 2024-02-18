from django.urls import path
from user import views

urlpatterns = [
    path('register/', views.register_handle, name='user_register'), # handle user registers
    path('login/', views.user_login, name='user_login'), # user login
    path('logout/', views.user_logout, name='user_logout'), # user logout
    path('deactive/', views.deactivate_account, name='user_deactivate_account'),
    path('profile_update/', views.update_profile, name='user_profile_update'),
    path('change_password/', views.change_password, name='user_change_password'),
    path('change_email/', views.change_email, name='user_change_email'),

]