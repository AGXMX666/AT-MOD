import os
import mimetypes
from django.contrib import admin
from django.contrib.staticfiles import finders
from django.urls import path, re_path, include
from . import views as main
from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound


def safe_static_serve(request, path, document_roots):
    """静态文件服务视图：不受 DEBUG 开关限制，按顺序在多个根目录与查找器中查找"""
    path = path.replace('\\', '/')
    candidates = []
    for root in document_roots:
        root = os.path.abspath(root)
        full_path = os.path.normpath(os.path.join(root, path))
        if full_path.startswith(os.path.normpath(root) + os.sep):
            candidates.append(full_path)

    # 兜底：使用 Django 静态文件查找器定位应用包内的静态目录
    # （如 SimpleUI 的 /static/admin/simpleui-x/，无需 collectstatic）
    # 注意：路由已吃掉 static/admin/ 前缀，查找器需要完整相对路径，故补回 admin/ 再试
    finder_candidates = [path]
    if not path.startswith('admin/'):
        finder_candidates.append('admin/' + path)
    for candidate_path in finder_candidates:
        try:
            found = finders.find(candidate_path)
        except Exception:
            found = None
        if found:
            candidates.append(os.path.abspath(found))
            break

    for full_path in candidates:
        if os.path.isfile(full_path):
            content_type, _ = mimetypes.guess_type(full_path)
            response = FileResponse(
                open(full_path, 'rb'),
                content_type=content_type or 'application/octet-stream',
            )
            response['X-Content-Type-Options'] = 'nosniff'
            return response
    return HttpResponseNotFound('File not found')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',main.home),
    path('home/',main.home),
    path('login/',main.logins),
    path('logout/',main.logout),
    path('user/',main.user,name='user'),
    path('register/',main.register),
    path('user/settings/',main.usersettings),
    path('user/settings/ChangeNickname/',main.ChangeNickname),
    path('user/settings/ChangePassword/',main.ChangePassword),
    path('user/settings/ChangeAvatar/',main.ChangeAvatar),
    path('user/settings/ChangeSignature/',main.ChangeSignature),
    path('user/settings/PermanentlyLogout/',main.PermanentlyLogout),
    path('user/settings/Resetuuid/',main.Resetuuid),
    path('user/settings/ClientOffline/',main.ClientOffline),
    path('api_v3/login/',main.login_api_v3),
    path('api_v3/function_user_api_v3/',main.function_user_api_v3),
    path('api_v3/function_info_api_v3/',main.function_info_api_v3),
    path('api_v3/bulletinboard_api_v3/', main.bulletinboard_api_v3),
    path('api_v3/upload_logfile_api_v3/', main.upload_file_api_v3),
    path('api_v3/GetAvatar_api_v3/', main.GetAvatar_api_v3),
    path('captcha/', include('captcha.urls')),
    path('refresh_captcha/', main.refresh_captcha),
    path('DeveloperDocumentation/', main.DeveloperDocumentation),
    path('Download/', main.Download),


]

# 静态文件服务：无论 DEBUG 开关均可使用
# 查找顺序：先 STATIC_ROOT（collectstatic 收集产物，含 admin/simpleui），
# 再 static/ 源目录（css/js/img 及运行时上传的 avatar/uploads），
# 最后回退到 Django 静态查找器（应用包内的静态目录，如 SimpleUI）
STATIC_ROOTS = [settings.STATIC_ROOT] + settings.STATICFILES_DIRS

urlpatterns += [
    re_path(r'^static/admin/(?P<path>.*)$', safe_static_serve,
            {'document_roots': [settings.STATIC_ADMIN] + STATIC_ROOTS},
            name='static_admin'),
    re_path(r'^static/(?P<path>.*)$', safe_static_serve,
            {'document_roots': STATIC_ROOTS}, name='static_files'),
]
