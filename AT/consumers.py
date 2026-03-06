import json
import datetime
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from database import models as database
from .online_state import ONLINE_USERS, ONLINE_INFO   # 内存字典
layer = get_channel_layer()
ONLINE_KEY_PREFIX = 'online:'


def online_key(uid: str) -> str:
    return f'{ONLINE_KEY_PREFIX}{uid}'
class UserConsumer(WebsocketConsumer):
    def connect(self):
        uuid_from_url = self.scope['url_route']['kwargs']['uuid'].strip().lower()
        try:
            user = database.users.objects.get(UniqueIdentification=uuid_from_url)
        except database.users.DoesNotExist:
            self.close()
            return
            
        if user.is_banned:
            self.close()
            return
            
        self.user = user
        self.key  = user.UniqueIdentification

        old_ch = ONLINE_USERS.pop(self.key, None)
        if old_ch and old_ch != self.channel_name:
            async_to_sync(layer.send)(old_ch, {"type": "force_close"})
        ONLINE_USERS[self.key] = self.channel_name
        ONLINE_INFO[self.key]   = {
            'id': user.id,
            'Account': user.Account,
            'nick_name': user.nick_name,
            'login_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        async_to_sync(layer.group_add)('online_admin', self.channel_name)
        async_to_sync(layer.group_send)(
            'online_admin',
            {'type': 'online_event', 'payload': list(ONLINE_INFO.values())}
        )

        self.accept()
        database.OperationLog.objects.create(
            Account=user.Account,
            uuid=user.UniqueIdentification,
            operation_type='connect',
            operation_time=datetime.datetime.now(),
            description=f'用户 {user.Account} 客户端上线'
        )
        print(f"[WebSocket] 用户 {user.Account} 上线")

    def disconnect(self, close_code):
        if ONLINE_USERS.get(self.key) == self.channel_name:
            ONLINE_USERS.pop(self.key, None)
            ONLINE_INFO.pop(self.key,  None)
            async_to_sync(layer.group_send)(
                'online_admin',
                {'type': 'online_event', 'payload': list(ONLINE_INFO.values())}
            )

        async_to_sync(layer.group_discard)('online_admin', self.channel_name)

        database.OperationLog.objects.create(
            Account=self.user.Account,
            uuid=self.user.UniqueIdentification,
            operation_type='disconnect',
            operation_time=datetime.datetime.now(),
            description=f'用户 {self.user.Account} 客户端下线'
        )
        print(f"[WebSocket] 用户 {self.user.Account} 下线")

    def force_close(self, event):
        self.close()

    def receive(self, text_data):
        data = json.loads(text_data)
        self.send(text_data=json.dumps({
            "from": self.user.nick_name,
            "message": data.get("message")
        }))

    def online_event(self, event):
        pass
