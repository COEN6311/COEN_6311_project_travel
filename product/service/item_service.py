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
