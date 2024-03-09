import json
import threading

from ..contans import redis_key_packages_with_items_data, redis_expire_packages_with_items_data
from ..serializers import FlightTicketSerializer, HotelSerializer, CustomPackageSerializer, ActivitySerializer
from ..models import CustomPackage, PackageItem, FlightTicket, Hotel, User, Activity

from utils.redis_connect import redis_client


def service_refresh_redis_packages_with_items():
    redis_client.delete(redis_key_packages_with_items_data)
    get_packages_with_items(None)


def refresh_redis_packages_with_items():
    thread = threading.Thread(target=service_refresh_redis_packages_with_items)
    thread.start()


def get_packages_with_items(user):
    for_agent = user is not None
    if not for_agent:
        cached_data = redis_client.get(redis_key_packages_with_items_data)
        if cached_data:
            return json.loads(cached_data)

    # Retrieve all packages  is_user=False prevent select user own package
    if for_agent:
        packages = CustomPackage.objects.filter(is_user=False, owner=user).prefetch_related('packageitem_set').all()
    else:
        packages = CustomPackage.objects.filter(is_user=False).prefetch_related('packageitem_set').all()
    package_serializer = CustomPackageSerializer(packages, many=True)

    # Retrieve all items
    if for_agent:
        flight_tickets = FlightTicket.objects.filter(owner=user).all()
    else:
        flight_tickets = FlightTicket.objects.all()
    if for_agent:
        hotels = Hotel.objects.filter(owner=user).all()
    else:
        hotels = Hotel.objects.all()
    if for_agent:
        activities = Activity.objects.filter(owner=user).all()
    else:
        activities = Activity.objects.all()

    # Serialize all items
    flight_ticket_serializer = FlightTicketSerializer(flight_tickets, many=True)
    hotel_serializer = HotelSerializer(hotels, many=True)
    activity_serializer = ActivitySerializer(activities, many=True)

    response_data = []

    # Append packages to response data with their details
    for package_data in package_serializer.data:
        response_data.append(package_data)

    # Append items to response data
    for item_data in flight_ticket_serializer.data:
        response_data.append(item_data)

    for item_data in hotel_serializer.data:
        response_data.append(item_data)

    for item_data in activity_serializer.data:
        response_data.append(item_data)

    if not for_agent:
        redis_client.set(redis_key_packages_with_items_data, json.dumps(response_data),
                         redis_expire_packages_with_items_data)
    return response_data
