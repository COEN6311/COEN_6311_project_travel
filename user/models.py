from django.db import models
from db.base_model import BaseModel
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


class UserManager(BaseUserManager):
    def create_user(self,  email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_agent', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True, verbose_name='user_email')
    is_active = models.BooleanField(default=True, verbose_name='active_status')
    is_agent = models.BooleanField(default=False, verbose_name='is_agent_status')
    is_staff = models.BooleanField(default=False, verbose_name='staff_status')
    first_name = models.CharField(default='', max_length=20, verbose_name='first_name')
    last_name = models.CharField(default='', max_length=20, verbose_name='last_name')
    mobile = models.CharField(default='', max_length=20, verbose_name='mobile')

    objects = UserManager()

    USERNAME_FIELD = 'email'

