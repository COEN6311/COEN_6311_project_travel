from django.db import models

class BaseModel(models.Model):
    '''模型抽象基类'''
    is_delete = models.BooleanField(default=False, verbose_name='Delete flag')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='Creation time')
    update_time = models.DateTimeField(auto_now=True, verbose_name='Update time')

    class Meta:
        abstract = True
