from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()

class EmailAuthToken(TokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            user = User.objects.get(email=key)
            if not user.check_password(self.request.data.get('password')):
                raise AuthenticationFailed('Invalid email or password')
            return (user, None)
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid email or password')
