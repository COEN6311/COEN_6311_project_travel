from product.models import Activity, Hotel, FlightTicket
from utils.emailSend import send_asynchronous_email


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


def send_order_payment_email(order_number, email):
    subject = "CONCORDIA TRAVEL:Your order has been paid successfully"
    # send email notification
    email_message = "Your order (order number: " + order_number + ") has been paid successfully. Thank you for choosing ConcordiaTravel."
    send_asynchronous_email(subject, email_message, email)


def send_order_notify_payment_email(order_number, email):
    subject = "CONCORDIA TRAVEL:Please pay your order"
    # send email notification
    email_message = "Your order (order number: " + order_number + ") has not been paid. We will keep the order for 5 minutes."
    send_asynchronous_email(subject, email_message, email)
