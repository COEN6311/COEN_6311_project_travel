from product.models import Activity, Hotel, FlightTicket


def handle_payment(card_number, security_code, amount):
    # todo real payment
    result = True

    return result


def calculate_prices(items):
    flight_price = 0
    activity_price = 0
    hotel_price = 0

    for item in items:
        if isinstance(item, FlightTicket):
            flight_price += item.price
        elif isinstance(item, Activity):
            activity_price += item.price
        elif isinstance(item, Hotel):
            hotel_price += item.price

    return flight_price, activity_price, hotel_price
