from cart.models import CartItem


def delete_cart_item(obj_id, type_param):
    package_items = CartItem.objects.filter(
        item_object_id=obj_id,
        type=type_param
    )
    package_items.delete()
