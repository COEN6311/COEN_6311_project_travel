from datetime import datetime

from order.constant import OrderStatus
from product.models import Activity, Hotel, FlightTicket
from utils.emailSend import send_asynchronous_email, send_custom_email


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
    send_custom_email(subject, email_message, [email])


def send_order_notify_payment_email(order_number, email):
    subject = "CONCORDIA TRAVEL:Please pay your order"
    # send email notification
    email_message = "Your order (order number: " + order_number + ") has not been paid. We will keep the order for 5 minutes."
    send_asynchronous_email(subject, email_message, email)


def get_order_status_by_date_span(start_date, end_date):
    today = datetime.now().date()

    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    if start_date <= today <= end_date:
        status = OrderStatus.TRAVELING.value
    elif today < start_date:
        status = OrderStatus.PENDING_DEPARTURE.value
    elif today > end_date:
        status = OrderStatus.COMPLETED.value
    return status
