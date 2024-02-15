from rest_framework.decorators import api_view
from rest_framework.response import Response
from user.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import reverse


def register(request):
    '''Display user registration page'''
    return Response({'message': 'Welcome to registration! Please fill in your registration information.'})

def is_strong_password(password):
    '''Check if the password meets the criteria for a strong password'''
    return (
        len(password) >= 8 and
        any(char.isupper() for char in password) and
        any(char.islower() for char in password) and
        any(char.isdigit() for char in password) and
        any(char in "!@#$%^&*" for char in password)
    )


@api_view(['POST'])
def register_handle(request):
    '''Process user registration'''
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    # Initialize result parameters
    result = False
    errorMsg = ""


    if not all([username, password, email]):
        # Check wether any data entry is empty
        if not username:
            errorMsg += 'Please enter your username！ '
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
                if User.objects.filter(username=username).exists():
                    errorMsg = 'The username already exists!'
                elif User.objects.filter(email=email).exists():
                    errorMsg = 'The email already exists!'
                else:
                    '''If everything above is fine, do registration and login'''
                    User.objects.create(username=username, password=password, email=email)
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                    result = True
        except ValidationError:
            errorMsg = 'The email format is invalid！'
        except Exception as e:
            print("Error:", e)  # print specific error message
            errorMsg = 'Registration failed！'

    if result:
        # Redirect the user to homepage with login status after successful registration
        return Response({'result': result, 'message': 'Registration successful!'}, status=201)
    else:
        return Response({'result': result, 'errorMsg': errorMsg}, status=400)

'''Enable user login'''
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from django.http import HttpResponse

def some_view(request):
    # Save the current page to session
    request.session['previous_page'] = request.path
    return HttpResponse("This is some view.")

@api_view(['POST'])
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Verify the username and password
    user = authenticate(request, username=username, password=password)
    if user is not None:
        # if login action succeed, then create or retrieve the user's token
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)  # Record the user's login status

        # Retrieve the previously browsed page, assuming the browsing history is saved in the user's session
        previous_page = request.session.get('previous_page')
        if previous_page:
            # Redirect to the previously browsed page
            return Response({'token': token.key, 'redirect_to': previous_page})
        else:
            # If no previous page,redirect to default page,eg:homepage
            return Response({'token': token.key, 'redirect_to': reverse('homepage')})
    else:
        # login failed
        return Response({'error': 'Username or password incorrect'}, status=400)



from django.contrib.auth import logout
'''enable user logout'''
@api_view(['POST'])
def user_logout(request):
    logout(request)
    return Response({'message': 'You have been logged out successfully.', 'redirect_to': 'homepage'})

@api_view(['POST'])
def deactivate_account(request):
    '''Deactivate user account'''
    username = request.data.get('username')
    if username:
        try:
            user = User.objects.get(username=username)
            user.is_active = False
            user.save()
            return Response({'message': 'User account deactivated successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found with the provided username'}, status=404)
    else:
        return Response({'error': 'Username not provided'}, status=400)