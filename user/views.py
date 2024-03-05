from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from user.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from user.serializers import UserSerializer
from user.service.send_emaill import send_verification_email, EmailValidationTimeOut, \
    send_verification_email_and_validate
from user.utils import is_strong_password
from utils.redis_connect import redis_client
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def confirm_email_click(request):
    click_sign = request.GET.get('click_sign')
    # save click_sign into Redis
    redis_client.set(click_sign, click_sign, 90)
    return Response({'You have confirmed. Please proceed with further actions on the platform.'})


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
        user_serializer = UserSerializer(user)
        response_data = {
            'result': True,
            'message': 'Registration successful!',
            'data': {
                'token': 'Token ' + token.key,
                'userInfo': user_serializer.data
            }
        }
        return JsonResponse(response_data)
    else:
        # login failed
        return Response({'result': False, 'error': 'Email or password incorrect'}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_handle(request):
    '''Process user registration'''
    global token
    password = request.data.get('password')
    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    mobile = request.data.get('mobile')
    skip_verify = request.data.get('skip_verify', '0')
    is_agent = request.data.get('is_agent', '0')
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
                errorMsg = ('The password must be at least 8 characters long and contain at least one uppercase letter'
                            ', one lowercase letter, one digit, and one special character (!@#$%^&*).')
            else:
                if User.objects.filter(email=email).exists():
                    errorMsg = 'The email already exists!'
                else:
                    send_verification_email_and_validate(email, skip_verify)
                    user_data = {'password': password, 'email': email}
                    if first_name:
                        user_data['first_name'] = first_name
                    if last_name:
                        user_data['last_name'] = last_name
                    if mobile:
                        user_data['mobile'] = mobile
                    user_data['is_agent'] = is_agent
                    User.objects.create_user(**user_data)
                    user = authenticate(request, username=email, password=password)
                    if user is not None:
                        token, _ = Token.objects.get_or_create(user=user)
                        login(request, user)  # Record the user's login status
                        result = True
        except ValidationError as e:
            logger.exception(e)
            errorMsg = 'The email format is invalid！'
        except EmailValidationTimeOut as e:
            logger.exception(e)
            errorMsg = 'Email validation timed out'
        except Exception as e:
            logger.exception(e)
            errorMsg = 'Registration failed！'

    if result:
        # Redirect the user to homepage with login status after successful registration
        user = User.objects.get(email=email)
        user_serializer = UserSerializer(user)
        response_data = {
            'result': True,
            'message': 'Registration successful!',
            'data': {
                'token': 'Token ' + token.key,
                'userInfo': user_serializer.data
            }
        }
        return JsonResponse(response_data)
    else:
        return Response({'result': result, 'errorMsg': errorMsg}, status=400)


from rest_framework.authtoken.models import Token


@api_view(['POST'])
def user_logout(request):
    try:
        token = request.auth
        token.delete()
    except (AttributeError, Token.DoesNotExist):
        return Response({'result': False, 'errorMsg': 'AttributeError'})
    logout(request)
    return Response(
        {'result': True, 'message': 'You have been logged out successfully.'})


@api_view(['POST'])
def deactivate_account(request):
    '''Deactivate user account'''
    email = request.data.get('email')
    password = request.data.get('password')
    skip_verify = request.data.get('skip_verify', '0')
    user = authenticate(request, username=email, password=password)
    if user is not None:
        try:
            send_verification_email_and_validate(email, skip_verify)
            user = User.objects.get(email=email)
            user.is_active = False
            user.save()
            return Response(
                {'result': True, 'message': 'User account deactivated successfully'})
        except User.DoesNotExist:
            return Response({'result': False, 'errorMsg': 'User not found with the provided email'}, status=404)
    else:
        return Response({'result': False, 'errorMsg': 'email or password invalid'}, status=400)


@api_view(['POST'])
def update_profile(request):
    '''Update user profile information, include first/last name, mobile, email and password'''
    update_fields = ['password', 'email', 'first_name', 'last_name', 'mobile', 'is_agent']
    success_messages = []
    update_detected = False  # Track if any update is detected
    skip_verify = request.data.get('skip_verify', '0')
    try:
        user = request.user
        send_verification_email_and_validate(user.email, skip_verify)
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
                        'result': False,
                        'errorMsg': 'The password must be at least 8 characters long and contain at least '
                                    'one uppercase letter,one lowercase letter, one digit, '
                                    'and one special character (!@#$%^&*).'}, status=400)
                else:
                    password_same = check_password(new_value, old_value)
                    if not password_same:
                        user.set_password(make_password(new_value))
                        success_messages.append('Password changed successfully')
                        update_detected = True
        user.save()
    except ValidationError:
        return Response({'result': False, 'errorMsg': 'Email invalid'}, status=400)
    except EmailValidationTimeOut as e:
        logger.exception(e)
        return Response({'result': False, 'errorMsg': 'Email validation timed out'}, status=400)
    if update_detected:
        return Response({'result': True, 'message': success_messages, 'data': {
            'userInfo': UserSerializer(user).data
        }})
    else:
        return Response({'result': True, 'message': 'No update detected'})
