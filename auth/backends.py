from django.contrib.auth import get_user_model

User = get_user_model()

from auth import get_user


class TokenBackend:
    def authenticate(self, request, pk):
        user, msg = get_user(request)
        if user.is_authenticated:
            if pk and user.id != pk:
                return None, 'The user_id does not match the token.'
        return user, msg
