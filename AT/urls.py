from django.contrib import admin
from django.urls import path, re_path, include
from . import views as main
from django.conf import settings
from django.views.static import serve
from django.conf.urls.static import static

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


]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns +=[re_path(r'^static/admin/(.*)$', serve,
        {'document_root': settings.STATIC_ADMIN}, name='static_admin'),]
