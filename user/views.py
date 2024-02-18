from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from user.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.shortcuts import reverse

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
    '''Update user profile information'''
    new_first_name = request.data.get('first_name')
    new_last_name = request.data.get('last_name')
    new_mobile = request.data.get('mobile')
    new_email = request.data.get('email')
    try:
        validate_email(new_email)
        user = request.user
        user.email = new_email
        User.first_name = new_first_name
        User.last_name = new_last_name
        User.mobile = new_mobile
        user.save()
    except ValidationError:
        return Response({'error': 'email invalid'}, status=400)
    return Response({'message': 'information update successfully'})

@api_view(['PUT'])
def change_password(request):
    '''change password of user account'''
    new_password = request.data.get('password')
    user = request.user
    if not is_strong_password(new_password):
        return Response({'The password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character (!@#$%^&*).'}, status=400)
    elif user.password == new_password:
        return Response({'message': 'The new and old passwords cannot be the same!'}, status=400)
    else:
        user.password = new_password
        user.save()
        return Response({'message': 'password changed successfully'})

@api_view(['PUT'])
def change_email(request):
    '''change email of user account'''
    user = request.user
    new_email = request.data.get('email')
    try:
        validate_email(new_email)
        if user.email == new_email:
            return Response({'message': 'The new and old email cannot be the same!'})
        else:
            user.email = new_email
            user.save()
    except ValidationError:
        return Response({'error': 'email invalid'}, status=400)
    return Response({'message': 'email update successfully'})