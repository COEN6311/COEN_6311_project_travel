from django.core.cache import cache


def get_item_detail(item_type, item_instance):
    if item_type == 1 or item_type == '1':
        return {
            'name': 'Flight Details',
            'items': [
                f'Destination: {item_instance.destination}',
                f'Flight number: {item_instance.flight_number}',
                f'Class: {item_instance.seat_class}',
                f'Departure: {item_instance.departure_time}',
                f'Arrival: {item_instance.arrival_time}',
            ],
            'type': 'flight',
            'price': float(item_instance.price)
        }
    elif item_type == 2 or item_type == '2':
        return {
            'name': 'Hotel Details',
            'items': [
                f'Hotel name: {item_instance.hotel_name}',
                f'Room: {item_instance.room}',
                f'Address: {item_instance.address}',
                f'Check-in: {item_instance.check_in_time.strftime("%H:%M") if item_instance.check_in_time else "N/A"}',
                f'Check-out: {item_instance.check_out_time.strftime("%H:%M") if item_instance.check_out_time else "N/A"}',
            ],
            'type': 'hotel',
            'price': float(item_instance.price)
        }
    elif item_type == 3 or item_type == '3':
        return {
            'name': item_instance.name,
            'items': [
                f'Event: {item_instance.event}',
                f'Location: {item_instance.location}',
                f'Address: {item_instance.address}',
                f'Time: {item_instance.time.strftime("%H:%M") if item_instance.time else None}',
            ],
            'type': 'activity',
            'price': float(item_instance.price)
        }
    else:
        raise ValueError(f"Unknown item type: {item_type}")


class detail_cache:
    def __init__(self):
        pass

    @staticmethod
    def get_cached_details(obj_id):
        """
        Get cached details for a given object ID.
        """
        return cache.get(f'package_details_{obj_id}')

    @staticmethod
    def cache_details(obj_id, details):
        cache.set(f'package_details_{obj_id}', details)
