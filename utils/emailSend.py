from django.core.mail import send_mail
from django.conf import settings


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
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
