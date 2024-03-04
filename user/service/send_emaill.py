import requests
import time
from utils.emailSend import send_custom_email
from utils.redis_connect import redis_client


# def generate_confirmation_link(email, click_token):
def generate_confirmation_link(click_sign):
    response = requests.get('https://api.ipify.org')
    ip_address = response.text
    # return f"http://{ip_address}/confirm?email={email}&token={click_token}"
    return f"http://{ip_address}:8000/user/confirm?click_sign={click_sign}"


def send_verification_email(email, click_sign):
    # Generate confirmation link
    confirmation_link = generate_confirmation_link(click_sign)
    # Send verification email
    subject = "Confirm your action"
    message = f"""
        <html>
            <body>
                <p>Please click the following link to confirm your action:</p>
                <p><a href="{confirmation_link}">Click here to confirm</a></p>
            </body>
        </html>
        """
    send_custom_email(subject, message, [email])


class EmailValidationTimeOut(Exception):
    def __init__(self, message="Email validation timed out"):
        self.message = message
        super().__init__(self.message)


def poll_redis_for_click_sign(email):
    # Poll Redis for click sign
    for _ in range(60):
        click_sign = redis_client.get(email)
        if click_sign is not None:
            redis_client.delete(email)
            return True
        else:
            time.sleep(1)  # Wait for 1 second before next polling
    return False


def send_verification_email_and_validate(email, skip_verify):

    click_token = email
    send_verification_email(email, click_token)

    #  skip_verify
    if skip_verify != '1':
        if not poll_redis_for_click_sign(click_token):
            raise EmailValidationTimeOut
