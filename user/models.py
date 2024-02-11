from django.db import models
from db.base_model import BaseModel
from utils.get_hash import get_hash



class AccountManager(models.Manager):
    def add_one_account(self, username, password, email):
        '''添加一个账户信息'''
        account = self.create(username=username, password=get_hash(password), email=email)
        # 3.返回account
        return account

    def get_one_account(self, username, password):
        '''根据用户名密码查找账户的信息'''
        try:
            account = self.get(username=username, password=get_hash(password))
        except self.model.DoesNotExist:
            # 账户不存在
            account = None
        return account

    # 创建一个账户Account类
class Account(BaseModel):
    '''用户模型类'''
    username = models.CharField(max_length=20, unique=True, verbose_name='username')
    password = models.CharField(max_length=40, verbose_name='password')
    email = models.EmailField(verbose_name='user_email')
    is_active = models.BooleanField(default=False, verbose_name='active_status')
    # 是不是可以在这里包含“customer”和“agent”的设置，用User_type区别？
    user_type = models.IntegerField(verbose_name='user_type')
    user_birthday = models.DateField(verbose_name='user_birthday')
    # 用户表的管理器
    objects = AccountManager()

    class Meta:
        db_table = 's_user_account'