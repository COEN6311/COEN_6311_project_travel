from product.models import FlightTicket, Hotel, Activity
from product.serializers import FlightTicketSerializer, HotelSerializer, ActivitySerializer


def get_item_serializer(item):
    if isinstance(item, FlightTicket):
        return FlightTicketSerializer
    elif isinstance(item, Hotel):
        return HotelSerializer
    elif isinstance(item, Activity):
        return ActivitySerializer
    else:
        raise ValueError(f'Unsupported item type: {type(item)}')


def get_json_structure_by_item(item):
    item_serializer = get_item_serializer(item)
    item_data = item_serializer(item).data
    return item_data


def get_item_by_category_and_id(category, item_id):
    try:
        if category == 'flight':
            item = FlightTicket.objects.get(id=item_id)
        elif category == 'hotel':
            item = Hotel.objects.get(id=item_id)
        elif category == 'activity':
            item = Activity.objects.get(id=item_id)
        else:
            raise ValueError(f'Unsupported item category: {category}')
        return item
    except (FlightTicket.DoesNotExist, Hotel.DoesNotExist, Activity.DoesNotExist):
        return None
