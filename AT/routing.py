from django.urls import re_path
from .consumers import UserConsumer
from database.admin_consumers import AdminOnlineConsumer

websocket_urlpatterns = [
    re_path(r'^ws/user/(?P<uuid>[0-9a-f]{16})/$', UserConsumer.as_asgi()),
    re_path(r'^ws/admin/online/$', AdminOnlineConsumer.as_asgi()),
]