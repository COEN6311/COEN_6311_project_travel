from django.db import models


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_delete=False)


class BaseModel(models.Model):
    is_delete = models.BooleanField(default=False, verbose_name='Delete flag')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='Creation time')
    update_time = models.DateTimeField(auto_now=True, verbose_name='Update time')

    objects = BaseModelManager()

    def soft_delete(self):
        self.is_delete = True
        self.save()

    class Meta:
        abstract = True
