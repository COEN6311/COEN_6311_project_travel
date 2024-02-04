from django.db import models

# Create your models here.
class BaseModel(models.Model):

    title = models.CharField(max_length=255, blank=False, null=False)