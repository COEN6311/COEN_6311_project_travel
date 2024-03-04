from rest_framework import serializers

from user.models import User

def generate_confirmation_link(click_sign):
    response = requests.get('https://api.ipify.org')
    ip_address = response.text
    # return f"http://{ip_address}/confirm?email={email}&token={click_token}"
    return f"http://{ip_address}:8000/user/confirm?click_sign={click_sign}"

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_agent = serializers.BooleanField()
    mobile = serializers.CharField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_agent', 'mobile']

# def generate_confirmation_link(email, click_token):



