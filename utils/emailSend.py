import threading

from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_custom_email(subject, message, recipient_list, from_email=settings.EMAIL_HOST_USER):
    """
    Sends a custom email.

    :param subject: Email subject
    :param message: Email body
    :param recipient_list: List of recipient email addresses
    :param from_email: Sender's email, defaults to EMAIL_HOST_USER from settings
    :return: None
    """
    try:
        logger.info(f"Sending email - Subject: {subject}, Message: {message}, Recipients: {recipient_list}")
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            html_message=message,
            # html_message=message,
            fail_silently=False,
        )
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise Exception(f"Failed to send email: {e}")


def send_asynchronous_email(subject, message, email):
    email_thread = threading.Thread(target=send_custom_email,
                                    args=((subject, message, [email])))
    email_thread.start()
