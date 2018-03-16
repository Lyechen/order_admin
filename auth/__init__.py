import requests
import time

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from utils.log import logger
from utils.response import res_code, ResCode

User = get_user_model()


def get_user(request):
    """
    Return the user model instance associated with the given request session.
    If no user is retrieved, return an instance of `AnonymousUser`.
    """

    user = AnonymousUser()

    token = request.META.get('HTTP_AUTHORIZATION')
    if not token:
        return (user, 'token不存在', 400, ResCode.Token_Missing)

    start = time.time()
    try:
        result = requests.get(settings.SSO_VERIFY, headers={'Authorization': token})
        status_code = result.status_code
        result = result.json()
    except Exception as ex:
        logger.error('SSO登录授权验证失败:' + str(ex))
        return (user, '服务器异常，登录授权验证失败', 500, ResCode.Token_Missing)
    end = time.time()
    logger.debug('sso verify time:{} ms'.format((end - start) * 1000))

    rescode = result.get('rescode')
    if rescode == res_code['success']:
        user_data = result.get('data')
        user = User()
        user.id = user_data.get('id')
        user.username = user_data.get('username')
        user.mobile = user_data.get('mobile')
        user.email = user_data.get('email')
        user.user_type = user_data.get('user_type')
        user.is_superuser = user_data.get('is_superuser')
        user.is_staff = user_data.get('is_staff')

    return (user, result.get('msg'), status_code, rescode)
