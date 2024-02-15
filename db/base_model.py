from django.db import models


class BaseModelManager(models.Manager):
    def get_queryset(self):
        """重写默认查询集，排除标记为删除的记录"""
        return super().get_queryset().filter(is_delete=False)

class BaseModel(models.Model):
    '''模型抽象基类'''
    is_delete = models.BooleanField(default=False, verbose_name='Delete flag')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='Creation time')
    update_time = models.DateTimeField(auto_now=True, verbose_name='Update time')

    objects = BaseModelManager()

    class Meta:
        abstract = True
