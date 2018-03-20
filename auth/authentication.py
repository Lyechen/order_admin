"""
Provides various authentication policies.
"""
from __future__ import unicode_literals

from rest_framework import exceptions

from auth import get_user
from utils.response import ResCode


class BaseAuthentication(object):
    """
    All authentication classes should extend BaseAuthentication.
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        raise NotImplementedError(".authenticate() must be overridden.")

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        pass


class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        request.user, msg, status_code, rescode = get_user(request)
        if not request.user.is_authenticated:
            detail = {
                'rescode': rescode,
                'msg': msg,
                'status_code': status_code
            }
            raise exceptions.AuthenticationFailed(detail)
        return (request.user, None)


class SupplierAuthentication(BaseAuthentication):
    def authenticate(self, request):
        request.user, msg, status_code, rescode = get_user(request)
        detail = {
            'rescode': rescode,
            'msg': msg,
            'status_code': status_code
        }
        if not request.user.is_authenticated:
            raise exceptions.APIException(detail)
        if request.user.user_type != 2:
            detail['status_code'] = 403
            detail['rescode'] = ResCode.Access_Denied
            detail['msg'] = '非供应商用户，无权限访问'
            raise exceptions.APIException(detail)
        return (request.user, None)


class AdminUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        request.user, msg, status_code, rescode = get_user(request)
        detail = {
            'rescode': rescode,
            'msg': msg,
            'status_code': status_code
        }
        if not request.user.is_authenticated:
            raise exceptions.APIException(detail)
        if not (request.user.is_staff or request.user.is_superuser):
            detail['status_code'] = 403
            detail['rescode'] = ResCode.Access_Denied
            detail['msg'] = '非管理员用户，无权限访问'
            raise exceptions.APIException(detail)
        return (request.user, None)
