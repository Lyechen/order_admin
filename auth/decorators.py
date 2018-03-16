from django.views.decorators.csrf import csrf_exempt

from functools import wraps

from utils.http import APIResponse, http_response
from auth import get_user


def token_required(view_func):
    """Decorator which ensures the user has provided a correct user and token pair."""

    @csrf_exempt
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        request.user, msg, status_code, rescode = get_user(request)
        if not request.user.is_authenticated:
            Response = http_response.get(status_code, APIResponse)
            return Response(rescode=rescode, msg=msg)
        return view_func(self, request, *args, **kwargs)

    return _wrapped_view
