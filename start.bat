@echo off
rem 关闭 DEBUG 启动（可用 DJANGO_DEBUG=True 重新开启）
set DJANGO_DEBUG=False
rem 本地用 http 访问时需关闭 Secure Cookie，否则浏览器不保存会话导致无法登录
set DJANGO_SESSION_COOKIE_SECURE=False
set DJANGO_CSRF_COOKIE_SECURE=False
python manage.py runserver