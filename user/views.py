import requests
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from user.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
import time
from utils.emailSend import send_custom_email
from django.conf import settings




import socket

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

@api_view(['GET'])
@permission_classes([AllowAny])
def confirm_registration(request):
    click_sign = request.GET.get('click_sign')
    # 存储click_sign到Redis
    redis_client.set(click_sign, click_sign,90)
    # 返回响应，可以是一个确认页面或者重定向到其他页面
    return Response({"message": "Registration confirmation send! Please continue your registration."})

class EmailValidationTimeOut(Exception):
    def __init__(self, message="Email validation timed out"):
        self.message = message
        super().__init__(self.message)

def poll_redis_for_click_sign(email):
    # Poll Redis for click sign
    for _ in range(60):
        click_sign = redis_client.get(email)
        if click_sign is not None:
            return True
        else:
            time.sleep(1)  # Wait for 1 second before next polling
    return False






def is_strong_password(password):
    '''Check if the password meets the criteria for a strong password'''
    return (
        len(password) >= 8 and
        any(char.isupper() for char in password) and
        any(char.islower() for char in password) and
        any(char.isdigit() for char in password) and
        any(char in "!@#$%^&*" for char in password)
    )

'''Enable user login'''
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    # username = request.data.get('username')
    username = request.data.get('email')
    password = request.data.get('password')

    # Verify the email and password
    user = authenticate(request, username=username, password=password)
    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        # if login action succeed, then create or retrieve the user's token
        login(request, user)  # Record the user's login status

        # Retrieve the previously browsed page, assuming the browsing history is saved in the user's session
        previous_page = request.session.get('previous_page')
        if previous_page:
            # Redirect to the previously browsed page
            return Response({'token': token.key, 'redirect_to': previous_page,'message': 'Login successful'})
        else:
            # If no previous page,redirect to default page,eg:homepage
            return Response({'token': token.key,'message': 'Login successful'})
            # return Response({'token': token.key, 'redirect_to': reverse('homepage')})
    else:
        # login failed
        return Response({'error': 'Email or password incorrect'}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_handle(request):
    '''Process user registration'''
    global token
    password = request.data.get('password')
    email = request.data.get('email')

    # Initialize result parameters
    result = False
    errorMsg = ""


    if not all([password, email]):
        # Check wether any data entry is empty
        if not password:
            errorMsg += 'Please enter your password！ '
        if not email:
            errorMsg += 'Please enter your email！'

    else:
        try:
            # Check the email format,if not valid, skip to 'except ValidationError'
            validate_email(email)
            if not is_strong_password(password):
                errorMsg = 'The password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character (!@#$%^&*).'
            else:
                if  User.objects.filter(email=email).exists():
                    errorMsg = 'The email already exists!'
                else:
                    '''If everything above is fine, do registration and login'''
                    # Send  email to the user containing a confirmation link, and start checking whether the
                    # user clicks the link. If clicked, proceed with registration; otherwise,
                    # raise an exception with the message "link timeout".
                    click_token = email
                    # Send verification email to the user
                    send_verification_email(email, click_token)
                    # Store click token in Redis to track user's verification status
                    # redis_client.set(click_token, 'clicked')

                    # Poll Redis for click sign
                    if not poll_redis_for_click_sign(click_token):
                        raise EmailValidationTimeOut
                    User.objects.create_user( password=password, email=email)
                    user = authenticate(request, username=email, password=password)
                    if user is not None:
                        token, _ = Token.objects.get_or_create(user=user)
                        login(request, user)  # Record the user's login status
                        result = True
        except ValidationError:
            errorMsg = 'The email format is invalid！'
        except Exception as e:
            print("Error:", e)  # print specific error message
            errorMsg = 'Registration failed！'

    if result:
        # Redirect the user to homepage with login status after successful registration
        return Response({'result': result, 'message': 'Registration successful!','redirect_to': 'homepage','token': token.key}, status=201,)
    else:
        return Response({'result': result, 'errorMsg': errorMsg}, status=400)



from rest_framework.authtoken.models import Token


@api_view(['POST'])
def user_logout(request):
    try:
        token = request.auth
        token.delete()
    except (AttributeError, Token.DoesNotExist):
        return Response({'message': 'AttributeError'})
    logout(request)
    return Response({'message': 'You have been logged out successfully.', 'redirect_to': 'homepage'})


@api_view(['POST'])
def deactivate_account(request):
    '''Deactivate user account'''
    email = request.data.get('email')
    password = request.data.get('password')
    # Verify the email and password
    user = authenticate(request, username=email, password=password)
    if user is not None:
        try:
            user = User.objects.get(email=email)
            user.is_active = False
            user.save()
            return Response({'message': 'User account deactivated successfully','redirect_to': 'homepage'})
        except User.DoesNotExist:
            return Response({'error': 'User not found with the provided email'}, status=404)
    else:
        return Response({'error': 'email or password invalid'}, status=400)



@api_view(['PUT'])
def update_profile(request):
    '''Update user profile information, include first/last name, mobile, email and password'''
    update_fields = ['password','email', 'first_name', 'last_name', 'mobile']
    success_messages = []
    update_detected = False  # Track if any update is detected
    try:
        user = request.user
        for field in update_fields:
            new_value = request.data.get(field)
            old_value = getattr(user, field)
            if field != 'password':
                if new_value is not None and new_value != old_value:
                    if field == 'email':
                        validate_email(new_value)
                    else:
                        setattr(user, field, new_value)
                    success_messages.append(f'{field.capitalize()} updated successfully')
                    update_detected = True  # Update detected
            elif field == 'password' and new_value is not None:
                if not is_strong_password(new_value):
                    return Response({
                                'error': 'The password must be at least 8 characters long and contain at least one uppercase letter,'
                                         ' one lowercase letter, one digit, and one special character (!@#$%^&*).'},status=400)
                else:
                    password_same=check_password(new_value, old_value)
                    if not password_same:
                        user.set_password(make_password(new_value))
                        success_messages.append('information changed successfully')
                        update_detected = True
        user.save()
    except ValidationError:
        return Response({'error': 'Email invalid'}, status=400)
    if update_detected:
        return Response({'message': success_messages})
    else:
        return Response({'message': 'No update detected'})
