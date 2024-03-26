from django.db import models


# Create your models here.

class Remark(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    user_id = models.IntegerField()  # User ID
    user_name = models.CharField(max_length=100)  # User's username
    order_number = models.CharField(max_length=100)  # Order number
    item_category = models.CharField(max_length=100)
    item_id = models.IntegerField()  # Item ID
    rating = models.IntegerField()  # Rating (star)
    comment = models.TextField(blank=True, null=True)  # Comment
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically record creation time
    modified_at = models.DateTimeField(auto_now=True)  # Automatically record modification time

    class Meta:
        unique_together = [['order_number', 'item_id', 'item_category']]

    @classmethod
    def create_or_update(cls, user_id, user_name, order_number, item_category, item_id, rating, comment):
        # Try to get existing Remark object
        remark, created = cls.objects.get_or_create(
            order_number=order_number,
            item_category=item_category,
            item_id=item_id,
            defaults={
                'user_id': user_id,
                'user_name': user_name,
                'rating': rating,
                'comment': comment
            }
        )

        # If the object already exists, update its attributes
        if not created:
            remark.user_id = user_id
            remark.user_name = user_name
            remark.rating = rating
            remark.comment = comment
            remark.save()

        return remark
