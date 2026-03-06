from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError
from django.contrib import auth
from database import models as database
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class SuppressDebugMiddleware(MiddlewareMixin):
    def __call__(self, request, *args, **kwargs):
        if request.path.startswith('/api_v3/') or request.path == '/favicon.ico':
            return self.get_response(request)

        if not hasattr(request, 'session'):
            return self.get_response(request)
        response = self.get_response(request)
        Account = request.session.get('Account', None)
        try:
            user_list = database.users.objects.get(Account=Account)
        except database.users.DoesNotExist:
            user_list = None

        if settings.DEBUG_PAGE_OFF:
            if response.status_code == 404:
                info = {"txt": "404!访问的页面不存在！", "tile": "404错误"}
                return render(request, "error.html", context={
                    "user_list": user_list,
                    "info": info,
                }, status=404)
            elif response.status_code == 403:
                info = {"txt": "403!你没有访问权限！", "tile": "403错误"}
                return render(request, "error.html", context={
                    "user_list": user_list,
                    "info": info,
                }, status=403)

        if 'Account' in request.session:
            try:
                if database.users.objects.get(Account=Account).is_banned:
                    info = {"txt": f'账号 "{Account}" 被封禁！', "tile": "账号封禁!"}
                    auth.logout(request)
                    return render(request, "error.html", context={
                        "info": info,
                        "user_list": user_list,
                    }, status=403)
            except database.users.DoesNotExist:
                pass

        return response

    def process_exception(self, request, exception):
        if request.path.startswith('/api_v3/'):
            return None
        if settings.DEBUG_PAGE_OFF:
            Account = request.session.get('Account', None)
            try:
                user_list = database.users.objects.get(Account=Account)
            except database.users.DoesNotExist:
                user_list = None
            info = {"txt": "500!服务器内部错误！", "tile": "500错误"}
            return render(request, "error.html", context={
                "user_list": user_list,
                "info": info,
            }, status=500)