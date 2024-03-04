import requests

from utils.emailSend import send_custom_email


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
    subject = "Confirm your registration"
    message = f"""
        <html>
            <body>
                <p>Please click the following link to confirm your registration:</p>
                <p><a href="{confirmation_link}">Click here to confirm</a></p>
            </body>
        </html>
        """
    send_custom_email(subject, message, [email])


class EmailValidationTimeOut(Exception):
    def __init__(self, message="Email validation timed out"):
        self.message = message
        super().__init__(self.message)
