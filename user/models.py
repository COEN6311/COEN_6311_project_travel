from django.db import models
from db.base_model import BaseModel
from utils.get_hash import get_hash
from django.contrib import admin
from .models import User


admin.site.register(User)


class UserManager(models.Manager):
    def add_one_account(self, username, password, email):
        user = self.create(username=username, password=get_hash(password), email=email)
        return user

    def get_one_account(self, username, password):
        '''Retrieve account information by username and password.'''
        try:
            user = self.get(username=username, password=get_hash(password))
        except self.model.DoesNotExist:
            user = None
        return user

class User(BaseModel):
    username = models.CharField(max_length=20, unique=True, verbose_name='username')
    password = models.CharField(max_length=100, verbose_name='password')
    email = models.EmailField(verbose_name='user_email')
    is_active = models.BooleanField(default=False, verbose_name='active_status')
    is_agent = models.BooleanField(default=False, verbose_name='is_agent_status')

    objects = UserManager()

    class Meta:
        db_table = 's_user_account'